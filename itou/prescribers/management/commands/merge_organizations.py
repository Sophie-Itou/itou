import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from itou.eligibility import models as eligibility_models
from itou.invitations import models as invitations_models
from itou.job_applications import models as job_applications_models
from itou.prescribers import models as prescribers_models
from itou.users import models as users_models


logger = logging.getLogger(__name__)

HELP_TEXT = """
    Merge a prescriber organization into another. All the data related to the
    first organization will be moved into the second organization. If there is
    no destination organization provided, the first organization will be deleted
    only if it is not attached to any data.
"""


def organization_merge_into(from_id, to_id):
    if from_id == to_id:
        raise ValueError(f"Unable to use the same organization as source and destination (ID {from_id}).")

    from_organization = prescribers_models.PrescriberOrganization.objects.get(pk=from_id)
    to_organization = prescribers_models.PrescriberOrganization.objects.get(pk=to_id)
    # Both SIRET and name should be identical
    logger.info(
        "MERGE organization 'ID %s - SIRET %s - %s'",
        from_id,
        from_organization.siret,
        from_organization.name,
    )

    job_applications = job_applications_models.JobApplication.objects.filter(sender_prescriber_organization_id=from_id)
    logger.info("| Job applications: %s", job_applications.count())

    # Move users not already present in organization destination
    members = prescribers_models.PrescriberMembership.objects.filter(organization_id=from_id).exclude(
        user__in=users_models.User.objects.filter(prescribermembership__organization_id=to_id)
    )
    logger.info("| Members: %s", members.count())

    diagnoses = eligibility_models.EligibilityDiagnosis.objects.filter(author_prescriber_organization_id=from_id)
    logger.info("| Diagnoses: %s", diagnoses.count())

    invitations = invitations_models.PrescriberWithOrgInvitation.objects.filter(organization_id=from_id)
    logger.info("| Invitations: %s", invitations.count())

    logger.info(
        "INTO organization 'ID %s - SIRET %s - %s'",
        to_id,
        to_organization.siret,
        to_organization.name,
    )

    with transaction.atomic():
        job_applications.update(sender_prescriber_organization_id=to_id)
        members.update(organization_id=to_id)
        diagnoses.update(author_prescriber_organization_id=to_id)
        invitations.update(organization_id=to_id)
        from_organization.delete()


class Command(BaseCommand):
    help = HELP_TEXT

    def add_arguments(self, parser):
        parser.add_argument(
            "--from",
            dest="from_id",
            metavar="FROM",
            type=int,
            help="ID of the prescriber organization to delete.",
            required=True,
        )
        parser.add_argument(
            "--to",
            dest="to_id",
            metavar="TO",
            type=int,
            help="ID of the prescriber organization to keep.",
            required=True,
        )

    def handle(self, *args, **options):
        organization_merge_into(options["from_id"], options["to_id"])