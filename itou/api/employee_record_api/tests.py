from unittest import mock

from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from itou.employee_record.factories import EmployeeRecordWithProfileFactory
from itou.employee_record.models import EmployeeRecord
from itou.job_applications.factories import JobApplicationFactory, JobApplicationWithCompleteJobSeekerProfileFactory
from itou.users.factories import DEFAULT_PASSWORD, SiaeStaffFactory
from itou.utils.mocks.address_format import mock_get_geocoding_data


ENDPOINT_URL = reverse("v1:employee-records-list")


class DummyEmployeeRecordAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()

    def test_happy_path(self):
        user = SiaeStaffFactory()
        # Create enough fake job applications so that the dummy endpoint returns the first 25 of them.
        JobApplicationFactory.create_batch(30)

        url = reverse("v1:token-auth")
        data = {"username": user.email, "password": DEFAULT_PASSWORD}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 200)

        token = response.json()["token"]

        url = reverse("v1:dummy-employee-records-list")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)

        # The dummy endpoint always returns 25 records, first page is 20 of them.
        self.assertEqual(response.json()["count"], 25)
        self.assertEqual(len(response.json()["results"]), 20)

        employee_record_json = response.json()["results"][0]
        self.assertIn("mesure", employee_record_json)
        self.assertIn("siret", employee_record_json)
        self.assertIn("numeroAnnexe", employee_record_json)
        self.assertIn("personnePhysique", employee_record_json)
        self.assertIn("passIae", employee_record_json["personnePhysique"])
        self.assertIn("adresse", employee_record_json)
        self.assertIn("situationSalarie", employee_record_json)


class EmployeeRecordAPIPermissionsTest(APITestCase):

    token_url = reverse("v1:token-auth")

    def setUp(self):
        self.client = APIClient()

        # We only care about status filtering: no coherence check on ASP return values
        job_application = JobApplicationWithCompleteJobSeekerProfileFactory()
        self.employee_record_ready = EmployeeRecordWithProfileFactory(
            job_application=job_application, status=EmployeeRecord.Status.READY
        )

        self.user = self.employee_record_ready.job_application.to_siae.members.first()
        self.unauthorized_user = SiaeStaffFactory()

    def test_permissions_ok_with_token(self):
        """
        Standard use-case: using external API client with token auth
        """
        data = {"username": self.user.email, "password": DEFAULT_PASSWORD}
        response = self.client.post(self.token_url, data, format="json")
        self.assertEqual(response.status_code, 200)

        token = response.json().get("token")
        self.assertIsNotNone(token)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        response = self.client.get(ENDPOINT_URL, format="json")

        # Result list found but empty
        self.assertEqual(response.status_code, 200)

    def test_permissions_ko_with_token(self):
        data = {"username": self.unauthorized_user.email, "password": DEFAULT_PASSWORD}
        response = self.client.post(self.token_url, data, format="json")
        self.assertEqual(response.status_code, 200)

        token = response.json().get("token")
        self.assertIsNotNone(token)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        response = self.client.get(ENDPOINT_URL, format="json")

        # Result list exists, but user is not member of any SIAE
        self.assertEqual(response.status_code, 403)

    def test_permission_ok_with_session(self):
        """
        A session authentication is valid to use the API (same security level as token)
        => Allows testing in DEV context
        """
        self.client.login(username=self.user.username, password=DEFAULT_PASSWORD)

        response = self.client.get(ENDPOINT_URL, format="json")
        self.assertEqual(response.status_code, 200)

    def test_permission_ko_with_session(self):
        self.client.login(username=self.unauthorized_user.username, password=DEFAULT_PASSWORD)

        response = self.client.get(ENDPOINT_URL, format="json")
        self.assertRedirects(response, reverse("account_logout"), status_code=302, target_status_code=200)


class EmployeeRecordAPIFetchListTest(APITestCase):

    # ASP fakers need this fixture
    fixtures = [
        "test_asp_INSEE_countries.json",
        "test_INSEE_communes.json",
    ]

    @mock.patch(
        "itou.common_apps.address.format.get_geocoding_data",
        side_effect=mock_get_geocoding_data,
    )
    def setUp(self, _mock):
        # We only care about status filtering: no coherence check on ASP return values
        job_application = JobApplicationWithCompleteJobSeekerProfileFactory()
        self.employee_record = EmployeeRecord.from_job_application(job_application)
        self.employee_record.update_as_ready()

        self.siae = job_application.to_siae
        self.siae_member = self.siae.members.first()
        self.user = job_application.job_seeker

    @mock.patch(
        "itou.common_apps.address.format.get_geocoding_data",
        side_effect=mock_get_geocoding_data,
    )
    def test_fetch_employee_record_list(self, _mock):
        """
        Fetch list of employee records with and without `status` query param
        """
        # Using session auth (same as token but less steps)
        self.client.login(username=self.siae_member.username, password=DEFAULT_PASSWORD)

        # Get list without filtering by status (PROCESSED)
        # note: there is no way to create a processed employee record
        # (and this is perfectly normal)
        self.employee_record.update_as_sent("RIAE_FS_20210410130000.json", 1)
        process_code, process_message = "0000", "La ligne de la fiche salarié a été enregistrée avec succès."

        # There should be no result at this point
        response = self.client.get(ENDPOINT_URL, format="json")

        self.assertEqual(response.status_code, 200)

        result = response.json()

        self.assertEqual(len(result.get("results")), 0)

        self.employee_record.update_as_accepted(process_code, process_message, "{}")
        response = self.client.get(ENDPOINT_URL, format="json")

        self.assertEqual(response.status_code, 200)

        result = response.json()

        self.assertEqual(len(result.get("results")), 1)
        self.assertContains(response, self.siae.siret)

        # status = SENT
        job_application = JobApplicationWithCompleteJobSeekerProfileFactory(to_siae=self.siae)
        employee_record_sent = EmployeeRecord.from_job_application(job_application=job_application)
        employee_record_sent.update_as_ready()

        # There should be no result at this point
        response = self.client.get(ENDPOINT_URL + "?status=SENT", format="json")

        self.assertEqual(response.status_code, 200)

        result = response.json()

        self.assertEqual(len(result.get("results")), 0)

        employee_record_sent.update_as_sent("RIAE_FS_20210410130001.json", 1)
        response = self.client.get(ENDPOINT_URL + "?status=SENT", format="json")

        self.assertEqual(response.status_code, 200)

        result = response.json()

        self.assertEqual(len(result.get("results")), 1)
        self.assertContains(response, self.siae.siret)

        # status = REJECTED
        job_application = JobApplicationWithCompleteJobSeekerProfileFactory(to_siae=self.siae)
        employee_record_rejected = EmployeeRecord.from_job_application(job_application=job_application)
        employee_record_rejected.update_as_ready()
        employee_record_rejected.update_as_sent("RIAE_FS_20210410130002.json", 1)

        # There should be no result at this point
        response = self.client.get(ENDPOINT_URL + "?status=REJECTED", format="json")
        self.assertEqual(response.status_code, 200)

        result = response.json()

        self.assertEqual(len(result.get("results")), 0)

        err_code, err_message = "12", "JSON Invalide"
        employee_record_rejected.update_as_rejected(err_code, err_message)

        # Status case is not important
        response = self.client.get(ENDPOINT_URL + "?status=rEjEcTeD", format="json")
        self.assertEqual(response.status_code, 200)

        result = response.json()

        self.assertEqual(len(result.get("results")), 1)
        self.assertContains(response, self.siae.siret)

    @mock.patch(
        "itou.common_apps.address.format.get_geocoding_data",
        side_effect=mock_get_geocoding_data,
    )
    def test_show_phone_email_api(self, _mock):
        # BUGFIX:
        # Test that employee phone number and email address are passed
        # to API serializer.
        self.client.login(username=self.siae_member.username, password=DEFAULT_PASSWORD)

        response = self.client.get(ENDPOINT_URL + "?status=READY", format="json")

        self.assertEqual(response.status_code, 200)

        json = response.json()

        self.assertEqual(len(json.get("results")), 1)

        results = json["results"][0]

        self.assertEqual(results.get("adresse").get("adrTelephone"), self.user.phone)
        self.assertEqual(results.get("adresse").get("adrMail"), self.user.email)
