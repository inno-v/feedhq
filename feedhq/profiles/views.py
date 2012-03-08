from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render
from django.views import generic

from .forms import ChangePasswordForm, ProfileForm
from ..decorators import login_required
from ..feeds.models import Feed


class ProfileView(generic.FormView):
    forms = {
        'password': ChangePasswordForm,
        'profile': ProfileForm,
    }
    template_name = 'auth/user_detail.html'

    def dispatch(self, request, *args, **kwargs):
        self.action = 'profile'
        if request.method == 'POST':
            self.action = request.POST.get('action', self.action)
        return super(ProfileView, self).dispatch(request, *args, **kwargs)

    def get_object(self):
        return self.request.user

    def get_form_class(self):
        return self.forms[self.action]

    def get_form_kwargs(self):
        kwargs = super(ProfileView, self).get_form_kwargs()
        kwargs.update({
            'instance': self.request.user,
        })
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super(ProfileView, self).get_context_data(**kwargs)
        ctx['%s_form' % self.action] = ctx['form']
        if self.action == 'password':
            ctx['profile_form'] = ProfileForm(**self.get_form_kwargs())
        else:
            ctx['password_form'] = ChangePasswordForm(**self.get_form_kwargs())
        del ctx['form']
        ctx.update({
            'categories': self.request.user.categories.count(),
            'feeds': Feed.objects.filter(
                category__user=self.request.user,
            ).count(),
            'entries': self.request.user.entries.count(),
        })
        return ctx

    def form_valid(self, form):
        form.save()
        messages.success(self.request, form.success_message)
        return redirect(reverse('profile'))
profile = login_required(ProfileView.as_view())


@login_required
def export(request):
    """OPML export"""
    response = render(request, 'profiles/opml_export.opml',
                      {'categories': request.user.categories.all()})
    response['Content-Disposition'] = 'attachment; filename=feedhq-export.opml'
    ctype = 'text/xml; charset=%s' % settings.DEFAULT_CONTENT_TYPE
    response['Content-Type'] = ctype
    return response
