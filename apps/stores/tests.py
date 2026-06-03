from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from apps.stores.models import Store, StorePartnerRequest

User = get_user_model()


class StorePendingWorkflowTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create an admin user for dashboard actions
        self.admin_user = User.objects.create_superuser(
            username='admin@example.com',
            email='admin@example.com',
            password='adminpassword',
            first_name='Admin',
            last_name='User',
            role=User.Role.ADMIN
        )

    def test_public_store_signup_pending_flow(self):
        """
        Verify that a public store signup creates inactive user/store,
        a pending request, and renders the pending template.
        """
        signup_url = reverse('store_signup')
        signup_data = {
            'store_name': 'Pending Shop',
            'address': '123 Pending St',
            'phone': '1234567890',
            'description': 'A beautiful pending store',
            'manager_first_name': 'John',
            'manager_last_name': 'Doe',
            'email': 'john.doe@example.com',
            'password': 'managerpassword123',
            'password_confirm': 'managerpassword123',
        }

        # Submit signup
        response = self.client.post(signup_url, signup_data)

        # Check response template used
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'stores/signup_pending.html')

        # Check User created and is inactive
        user = User.objects.filter(email='john.doe@example.com').first()
        self.assertIsNotNone(user)
        self.assertFalse(user.is_active)
        self.assertEqual(user.role, User.Role.MANAGER)
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Doe')

        # Check Store created and is inactive
        store = Store.objects.filter(manager=user).first()
        self.assertIsNotNone(store)
        self.assertFalse(store.is_active)
        self.assertEqual(store.name, 'Pending Shop')
        self.assertEqual(store.address, '123 Pending St')

        # Check StorePartnerRequest created and is pending
        partner_request = StorePartnerRequest.objects.filter(email='john.doe@example.com').first()
        self.assertIsNotNone(partner_request)
        self.assertEqual(partner_request.status, StorePartnerRequest.Status.PENDING)
        self.assertEqual(partner_request.store_name, 'Pending Shop')

    def test_inactive_user_login_attempts(self):
        """
        Verify that an inactive user trying to log in with correct credentials
        gets a friendly message, but wrong credentials gets generic error.
        """
        # Create an inactive user manually
        inactive_user = User.objects.create_user(
            username='inactive@example.com',
            email='inactive@example.com',
            password='secretpassword',
            first_name='Inactive',
            last_name='User',
            role=User.Role.MANAGER
        )
        inactive_user.is_active = False
        inactive_user.save()

        login_url = reverse('login')

        # 1. Correct password attempt
        response = self.client.post(login_url, {
            'email': 'inactive@example.com',
            'password': 'secretpassword'
        }, follow=True)
        messages = list(response.context.get('messages', []))
        self.assertTrue(any("compte est en cours d'examen" in str(msg) for msg in messages))

        # 2. Incorrect password attempt
        response = self.client.post(login_url, {
            'email': 'inactive@example.com',
            'password': 'wrongpassword'
        }, follow=True)
        messages = list(response.context.get('messages', []))
        self.assertTrue(any("Identifiants incorrects" in str(msg) for msg in messages))

    def test_admin_approve_existing_inactive_user(self):
        """
        Verify that when admin approves a request where the inactive user already exists,
        it activates the user and store, and sends a password-less email.
        """
        # Create inactive user, store, and pending request
        inactive_user = User.objects.create_user(
            username='partner@example.com',
            email='partner@example.com',
            password='partnerpassword',
            first_name='Partner',
            last_name='Gérant',
            role=User.Role.MANAGER
        )
        inactive_user.is_active = False
        inactive_user.save()

        store = Store.objects.create(
            manager=inactive_user,
            name='Partner Shop',
            is_active=False
        )

        partner_request = StorePartnerRequest.objects.create(
            first_name='Partner',
            last_name='Gérant',
            store_name='Partner Shop',
            email='partner@example.com',
            status=StorePartnerRequest.Status.PENDING
        )

        # Log in admin to access approval page
        self.client.login(email='admin@example.com', password='adminpassword')

        # Approve the request
        detail_url = reverse('store_request_detail', args=[partner_request.pk])
        response = self.client.post(detail_url, follow=True)

        # Check request status updated to APPROVED
        partner_request.refresh_from_db()
        self.assertEqual(partner_request.status, StorePartnerRequest.Status.APPROVED)

        # Check User and Store activated
        inactive_user.refresh_from_db()
        self.assertTrue(inactive_user.is_active)
        store.refresh_from_db()
        self.assertTrue(store.is_active)

        # Verify confirmation email sent (without password generated)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['partner@example.com'])
        self.assertIn("Votre compte est désormais actif", email.body)
        self.assertIn("[Celui choisi lors de votre demande d'inscription]", email.body)
        self.assertNotIn("Mot de passe : ", email.body.replace("[Celui choisi lors de votre demande d'inscription]", ""))

    def test_admin_approve_non_existent_user_fallback(self):
        """
        Verify that when admin approves a request where the user does not exist,
        it creates the user and store with a random password and emails it.
        """
        partner_request = StorePartnerRequest.objects.create(
            first_name='New',
            last_name='User',
            store_name='New Shop',
            email='new.partner@example.com',
            status=StorePartnerRequest.Status.PENDING
        )

        # Log in admin to access approval page
        self.client.login(email='admin@example.com', password='adminpassword')

        # Approve the request
        detail_url = reverse('store_request_detail', args=[partner_request.pk])
        response = self.client.post(detail_url, follow=True)

        # Check request status updated to APPROVED
        partner_request.refresh_from_db()
        self.assertEqual(partner_request.status, StorePartnerRequest.Status.APPROVED)

        # Check User and Store created and active
        user = User.objects.filter(email='new.partner@example.com').first()
        self.assertIsNotNone(user)
        self.assertTrue(user.is_active)

        store = Store.objects.filter(manager=user).first()
        self.assertIsNotNone(store)
        self.assertTrue(store.is_active)

        # Verify credentials email sent (with password generated)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['new.partner@example.com'])
        self.assertIn("Voici vos accès pour vous connecter", email.body)
        self.assertNotIn("[Celui choisi lors de votre demande d'inscription]", email.body)

    def test_admin_dashboard_shows_pending_store_requests_count(self):
        """
        Verify that the admin dashboard context contains the correct count of
        pending store requests, and the page renders it.
        """
        # Create 2 pending requests
        StorePartnerRequest.objects.create(
            first_name='P1', last_name='L1', store_name='Shop 1', email='p1@example.com', status=StorePartnerRequest.Status.PENDING
        )
        StorePartnerRequest.objects.create(
            first_name='P2', last_name='L2', store_name='Shop 2', email='p2@example.com', status=StorePartnerRequest.Status.PENDING
        )
        # Create 1 approved request
        StorePartnerRequest.objects.create(
            first_name='P3', last_name='L3', store_name='Shop 3', email='p3@example.com', status=StorePartnerRequest.Status.APPROVED
        )

        # Log in admin
        self.client.login(email='admin@example.com', password='adminpassword')

        # Get dashboard
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['pending_store_requests'], 2)
        self.assertContains(response, "Demandes partenaires")
