try:
    from django.contrib.auth.mixins import AccessMixin
except ImportError:
    from django.conf import settings
    from django.contrib.auth import REDIRECT_FIELD_NAME
    from django.contrib.auth.views import redirect_to_login
    from django.core.exceptions import ImproperlyConfigured, PermissionDenied
    from django.utils.encoding import force_text

    class AccessMixin(object):  # noqa
        """
        Abstract CBV mixin that gives access mixins the same customizable
        functionality.
        """
        login_url = None
        permission_denied_message = ''
        raise_exception = False
        redirect_field_name = REDIRECT_FIELD_NAME

        def get_login_url(self):
            """
            Override this method to override the login_url attribute.
            """
            login_url = self.login_url or settings.LOGIN_URL
            if not login_url:
                raise ImproperlyConfigured(
                    '{0} is missing the login_url attribute. Define {0}.login_url, settings.LOGIN_URL, or override '
                    '{0}.get_login_url().'.format(self.__class__.__name__)
                )
            return force_text(login_url)

        def get_permission_denied_message(self):
            """
            Override this method to override the permission_denied_message attribute.
            """
            return self.permission_denied_message

        def get_redirect_field_name(self):
            """
            Override this method to override the redirect_field_name attribute.
            """
            return self.redirect_field_name

        def handle_no_permission(self):
            if self.raise_exception:
                raise PermissionDenied(self.get_permission_denied_message())
            return redirect_to_login(self.request.get_full_path(), self.get_login_url(), self.get_redirect_field_name())


try:
    from django.contrib.auth.mixins import LoginRequiredMixin
except ImportError:

    class LoginRequiredMixin(AccessMixin):  # noqa
        """
        CBV mixin which verifies that the current user is authenticated.
        """
        def dispatch(self, request, *args, **kwargs):
            if not request.user.is_authenticated():
                return self.handle_no_permission()
            return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)


try:
    from django.contrib.auth.mixins import PermissionRequiredMixin
except ImportError:
    from django.utils import six
    from django.core.exceptions import ImproperlyConfigured  # noqa

    class PermissionRequiredMixin(AccessMixin):  # noqa
        """
        CBV mixin which verifies that the current user has all specified
        permissions.
        """
        permission_required = None

        def get_permission_required(self):
            """
            Override this method to override the permission_required attribute.
            Must return an iterable.
            """
            if self.permission_required is None:
                raise ImproperlyConfigured(
                    '{0} is missing the permission_required attribute. Define {0}.permission_required, or override '
                    '{0}.get_permission_required().'.format(self.__class__.__name__)
                )
            if isinstance(self.permission_required, six.string_types):
                perms = (self.permission_required, )
            else:
                perms = self.permission_required
            return perms

        def has_permission(self):
            """
            Override this method to customize the way permissions are checked.
            """
            perms = self.get_permission_required()
            return self.request.user.has_perms(perms)

        def dispatch(self, request, *args, **kwargs):
            if not self.has_permission():
                return self.handle_no_permission()
            return super(PermissionRequiredMixin, self).dispatch(request, *args, **kwargs)


try:
    from django.contrib.auth.mixins import UserPassesTestMixin
except ImportError:

    class UserPassesTestMixin(AccessMixin):  # noqa
        """
        CBV Mixin that allows you to define a test function which must return True
        if the current user can access the view.
        """

        def test_func(self):
            raise NotImplementedError(
                '{0} is missing the implementation of the test_func() method.'.format(self.__class__.__name__)
            )

        def get_test_func(self):
            """
            Override this method to use a different test_func method.
            """
            return self.test_func

        def dispatch(self, request, *args, **kwargs):
            user_test_result = self.get_test_func()()
            if not user_test_result:
                return self.handle_no_permission()
            return super(UserPassesTestMixin, self).dispatch(request, *args, **kwargs)
