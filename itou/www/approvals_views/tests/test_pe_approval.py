from dateutil.relativedelta import relativedelta
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from itou.approvals.factories import ApprovalFactory, PoleEmploiApprovalFactory
from itou.approvals.models import Approval
from itou.job_applications.factories import JobApplicationWithApprovalFactory
from itou.job_applications.models import JobApplicationWorkflow
from itou.siaes.factories import SiaeMembershipFactory
from itou.users.factories import DEFAULT_PASSWORD, JobSeekerFactory
from itou.users.models import User


class PoleEmploiApprovalSearchTest(TestCase):
    def setUp(self):
        self.url = reverse("approvals:pe_approval_search")

    def set_up_pe_approval(self):
        # pylint: disable=attribute-defined-outside-init
        self.job_application = JobApplicationWithApprovalFactory(state=JobApplicationWorkflow.STATE_ACCEPTED)
        self.siae = self.job_application.to_siae
        self.siae_user = self.job_application.to_siae.members.first()
        self.approval = self.job_application.approval
        self.job_seeker = self.job_application.job_seeker
        self.pe_approval = PoleEmploiApprovalFactory()

    def test_default(self):
        """
        The search for PE approval screen should not crash ;)
        """
        siae = SiaeMembershipFactory()
        self.client.login(username=siae.user.email, password=DEFAULT_PASSWORD)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rechercher un agrément Pôle emploi")

    def test_nominal(self):
        """
        The search for PE approval screen should display the job seeker's name
        if the PE approval number that was searched for has a matching PE approval
        """
        self.set_up_pe_approval()
        self.client.login(username=self.siae_user.email, password=DEFAULT_PASSWORD)

        response = self.client.get(self.url, {"number": self.pe_approval.number})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Agrément trouvé")

    def test_number_length(self):
        """
        Only two forms of approval numbers are accepted
        """
        siae = SiaeMembershipFactory()
        self.client.login(username=siae.user.email, password=DEFAULT_PASSWORD)

        invalid_number = "1234567890123"
        assert len(invalid_number) == 13

        response = self.client.get(self.url, {"number": invalid_number})
        self.assertContains(response, "Seuls les numéros d'agrément de 12 ou 15 chiffres sont valides.", html=True)

    def test_no_results(self):
        """
        The search for PE approval screen should display that there is no results
        if a PE approval number was searched for but nothing was found
        """
        siae = SiaeMembershipFactory()
        self.client.login(username=siae.user.email, password=DEFAULT_PASSWORD)

        response = self.client.get(self.url, {"number": 123123123123})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nous n'avons pas trouvé d'agrément")

    def test_approval_in_the_future(self):
        """
        The search for PE approval screen should display that there is no results
        if a PE approval number was searched for but it is in the future
        """
        today = timezone.now().date()

        pe_approval = PoleEmploiApprovalFactory(start_at=today + relativedelta(days=10))

        job_application = JobApplicationWithApprovalFactory(state=JobApplicationWorkflow.STATE_ACCEPTED)
        siae_user = job_application.to_siae.members.first()
        self.client.login(username=siae_user.email, password=DEFAULT_PASSWORD)

        response = self.client.get(self.url, {"number": pe_approval.number})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nous n'avons pas trouvé d'agrément")

    def test_has_matching_pass_iae(self):
        """
        The search for PE approval screen should redirect to the matching job application details screen if the
        number matches a PASS IAE attached to a job_application
        """
        self.set_up_pe_approval()

        self.client.login(username=self.siae_user.email, password=DEFAULT_PASSWORD)

        response = self.client.get(self.url, {"number": self.approval.number})
        self.assertEqual(response.status_code, 302)

        next_url = reverse("apply:details_for_siae", kwargs={"job_application_id": self.job_application.id})
        self.assertEqual(response.url, next_url)

    def test_has_matching_pass_iae_that_belongs_to_another_siae(self):
        """
        Make sure to NOT to redirect to job applications belonging to other SIAEs,
        as this would produce a 404.
        """

        # Create a job application with a PASS IAE created from a `PoleEmploiApproval`
        # that belongs to another siae.
        self.set_up_pe_approval()

        job_seeker = JobSeekerFactory()
        pe_approval = PoleEmploiApprovalFactory()
        job_application = JobApplicationWithApprovalFactory(
            state=JobApplicationWorkflow.STATE_ACCEPTED,
            approval__number=pe_approval.number,
            approval__user=job_seeker,
            job_seeker=job_seeker,
        )

        another_siae = job_application.to_siae
        self.assertNotEqual(another_siae, self.siae)

        # This is the current user (NOT a member of `another_siae`).
        self.client.login(username=self.siae_user.email, password=DEFAULT_PASSWORD)

        # The current user should not be redirected to the details of `job_application` because
        # it belongs to `another_siae`. He should get a 302 instead with an error message.
        response = self.client.get(self.url, {"number": job_application.approval.number})
        self.assertEqual(response.status_code, 302)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            f"Le numéro {pe_approval.number_with_spaces} est déjà utilisé par un autre employeur.",
        )

    def test_unlogged_is_not_authorized(self):
        """
        It is not possible to access the search for PE approval screen unlogged
        """

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        next_url = reverse("account_login")
        self.assertIn(next_url, response.url)

    def test_as_job_seeker_is_not_authorized(self):
        """
        The search for PE approval screen as job seeker is not authorized
        """
        job_application = JobApplicationWithApprovalFactory(state=JobApplicationWorkflow.STATE_ACCEPTED)
        self.client.login(username=job_application.job_seeker.email, password=DEFAULT_PASSWORD)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)


class PoleEmploiApprovalSearchUserTest(TestCase):
    def setUp(self):
        self.job_application = JobApplicationWithApprovalFactory(state=JobApplicationWorkflow.STATE_ACCEPTED)
        self.siae = self.job_application.to_siae
        self.siae_user = self.job_application.to_siae.members.first()
        self.approval = self.job_application.approval
        self.pe_approval = PoleEmploiApprovalFactory()

    def test_nominal(self):
        """
        The search for PE approval screen should redirect to the matching job application details screen if the
        number matches a PASS IAE attached to a job_application
        """
        self.client.login(username=self.siae_user.email, password=DEFAULT_PASSWORD)

        url = reverse("approvals:pe_approval_search_user", kwargs={"pe_approval_id": self.pe_approval.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.pe_approval.last_name)
        self.assertContains(response, self.pe_approval.first_name)

    def test_invalid_pe_approval(self):
        """
        The search for PE approval screen should redirect to the matching job application details screen if the
        number matches a PASS IAE attached to a job_application
        """
        self.client.login(username=self.siae_user.email, password=DEFAULT_PASSWORD)

        url = reverse("approvals:pe_approval_search_user", kwargs={"pe_approval_id": 123})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class PoleEmploiApprovalCreateTest(TestCase):
    def setUp(self):
        self.job_application = JobApplicationWithApprovalFactory(state=JobApplicationWorkflow.STATE_ACCEPTED)
        self.siae = self.job_application.to_siae
        self.siae_user = self.job_application.to_siae.members.first()
        self.approval = self.job_application.approval
        self.job_seeker = self.job_application.job_seeker
        self.pe_approval = PoleEmploiApprovalFactory()

    def test_from_new_user(self):
        """
        When the user does not exist for the suggested email, it is created as well as the approval
        """
        initial_approval_count = Approval.objects.count()
        initial_user_count = User.objects.count()
        self.client.login(username=self.siae_user.email, password=DEFAULT_PASSWORD)
        email = "some.new@email.com"
        url = reverse("approvals:pe_approval_create", kwargs={"pe_approval_id": self.pe_approval.id})
        params = {"email": email}
        response = self.client.post(url, params)

        new_user = User.objects.get(email=email)

        self.assertTrue(new_user.approvals_wrapper.has_valid)
        self.assertEqual(new_user.approvals_wrapper.latest_approval.number, self.pe_approval.number[:12])
        self.assertEqual(response.status_code, 302)
        self.assertTrue(new_user.last_accepted_job_application is not None)
        next_url = reverse(
            "apply:details_for_siae", kwargs={"job_application_id": new_user.last_accepted_job_application.id}
        )
        self.assertEqual(response.url, next_url)
        self.assertEqual(Approval.objects.count(), initial_approval_count + 1)
        self.assertEqual(User.objects.count(), initial_user_count + 1)

    def test_from_existing_user_without_approval(self):
        """
        When an existing user has no valid approval, it is possible to import a Pole Emploi Approval
        """
        initial_approval_count = Approval.objects.count()
        job_seeker = JobSeekerFactory()
        self.client.login(username=self.siae_user.email, password=DEFAULT_PASSWORD)

        url = reverse("approvals:pe_approval_create", kwargs={"pe_approval_id": self.pe_approval.id})
        params = {"email": job_seeker.email}
        response = self.client.post(url, params)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Approval.objects.count(), initial_approval_count + 1)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            "L'agrément Pôle emploi a bien été importé, vous pouvez désormais le prolonger ou le suspendre.",
        )

    def test_when_pole_emploi_approval_has_already_been_imported(self):
        """
        When the PoleEmploiApproval has already been imported, we are redirected to its page
        """
        self.job_application = JobApplicationWithApprovalFactory(
            state=JobApplicationWorkflow.STATE_ACCEPTED, approval=ApprovalFactory(number=self.pe_approval.number[:12])
        )

        initial_approval_count = Approval.objects.count()
        job_seeker = JobSeekerFactory()
        self.client.login(username=self.siae_user.email, password=DEFAULT_PASSWORD)

        url = reverse("approvals:pe_approval_create", kwargs={"pe_approval_id": self.pe_approval.id})
        params = {"email": job_seeker.email}
        response = self.client.post(url, params)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Approval.objects.count(), initial_approval_count)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Cet agrément Pôle emploi a déja été importé.")

    def test_from_existing_user_with_approval(self):
        """
        When an existing user already has a valid approval, it is not possible to import a Pole Emploi Approval
        """
        self.assertTrue(self.job_seeker.approvals_wrapper.has_valid)

        initial_approval_count = Approval.objects.count()
        self.client.login(username=self.siae_user.email, password=DEFAULT_PASSWORD)

        url = reverse("approvals:pe_approval_create", kwargs={"pe_approval_id": self.pe_approval.id})
        params = {"email": self.job_seeker.email}

        response = self.client.post(url, params)

        self.assertEqual(Approval.objects.count(), initial_approval_count)
        self.assertEqual(response.status_code, 302)
        next_url = reverse("approvals:pe_approval_search_user", kwargs={"pe_approval_id": self.pe_approval.id})
        self.assertEqual(response.url, next_url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Le candidat associé à cette adresse email a déja un PASS IAE valide.")