from __future__ import print_function, unicode_literals

import json

from liberapay.testing import EUR, Harness


class Tests(Harness):

    def test_anonymous(self):
        alice = self.make_participant('alice', balance=100)
        bob = self.make_participant('bob')

        alice.set_tip_to(bob, EUR('1.00'))

        data = json.loads(self.client.GET('/bob/public.json').text)
        assert data['receiving'] == {"amount": "1.00", "currency": "EUR"}
        assert 'my_tip' not in data

        data = json.loads(self.client.GET('/alice/public.json').text)
        assert data['giving'] == {"amount": "1.00", "currency": "EUR"}

    def test_anonymous_gets_null_giving_if_user_anonymous(self):
        alice = self.make_participant('alice', balance=100, hide_giving=True)
        bob = self.make_participant('bob')
        alice.set_tip_to(bob, EUR('1.00'))
        data = json.loads(self.client.GET('/alice/public.json').text)

        assert data['giving'] == None

    def test_anonymous_gets_null_receiving_if_user_anonymous(self):
        alice = self.make_participant('alice', balance=100, hide_receiving=True)
        bob = self.make_participant('bob')
        alice.set_tip_to(bob, EUR('1.00'))
        data = json.loads(self.client.GET('/alice/public.json').text)

        assert data['receiving'] == None

    def test_anonymous_does_not_get_goal_if_user_regifts(self):
        self.make_participant('alice', balance=100, goal=EUR(0))
        data = json.loads(self.client.GET('/alice/public.json').text)
        assert 'goal' not in data

    def test_anonymous_gets_null_goal_if_user_has_no_goal(self):
        self.make_participant('alice', balance=100)
        data = json.loads(self.client.GET('/alice/public.json').text)
        assert data['goal'] == None

    def test_anonymous_gets_user_goal_if_set(self):
        self.make_participant('alice', balance=100, goal=EUR('1.00'))
        data = json.loads(self.client.GET('/alice/public.json').text)
        assert data['goal'] == {"amount": "1.00", "currency": "EUR"}

    def test_authenticated_user_gets_their_tip(self):
        alice = self.make_participant('alice', balance=100)
        bob = self.make_participant('bob')

        alice.set_tip_to(bob, EUR('1.00'))

        raw = self.client.GET('/bob/public.json', auth_as=alice).text

        data = json.loads(raw)

        assert data['receiving'] == {"amount": "1.00", "currency": "EUR"}
        assert data['my_tip'] == {"amount": "1.00", "currency": "EUR"}

    def test_authenticated_user_doesnt_get_other_peoples_tips(self):
        alice = self.make_participant('alice', balance=100)
        bob = self.make_participant('bob', balance=100)
        carl = self.make_participant('carl', balance=100)
        dana = self.make_participant('dana')

        alice.set_tip_to(dana, EUR('1.00'))
        bob.set_tip_to(dana, EUR('3.00'))
        carl.set_tip_to(dana, EUR('12.00'))

        raw = self.client.GET('/dana/public.json', auth_as=alice).text

        data = json.loads(raw)

        assert data['receiving'] == {"amount": "16.00", "currency": "EUR"}
        assert data['my_tip'] == {"amount": "1.00", "currency": "EUR"}

    def test_authenticated_user_gets_zero_if_they_dont_tip(self):
        alice = self.make_participant('alice', balance=100)
        bob = self.make_participant('bob', balance=100)
        carl = self.make_participant('carl')

        bob.set_tip_to(carl, EUR('3.00'))

        raw = self.client.GET('/carl/public.json', auth_as=alice).text

        data = json.loads(raw)

        assert data['receiving'] == {"amount": "3.00", "currency": "EUR"}
        assert data['my_tip'] == {"amount": "0.00", "currency": "EUR"}

    def test_authenticated_user_gets_self_for_self(self):
        alice = self.make_participant('alice', balance=100)
        bob = self.make_participant('bob')

        alice.set_tip_to(bob, EUR('3.00'))

        raw = self.client.GET('/bob/public.json', auth_as=bob).text

        data = json.loads(raw)

        assert data['receiving'] == {"amount": "3.00", "currency": "EUR"}
        assert data['my_tip'] == 'self'

    def test_access_control_allow_origin_header_is_asterisk(self):
        self.make_participant('alice', balance=100)
        response = self.client.GET('/alice/public.json')

        assert response.headers[b'Access-Control-Allow-Origin'] == b'*'

    def test_jsonp_works(self):
        alice = self.make_participant('alice', balance=100)
        bob = self.make_participant('bob')

        alice.set_tip_to(bob, EUR('3.00'))

        raw = self.client.GET('/bob/public.json?callback=foo', auth_as=bob).text

        assert raw == '''\
/**/ foo({
    "avatar": null,
    "elsewhere": {
        "github": {
            "id": %(elsewhere_id)s,
            "user_id": "%(user_id)s",
            "user_name": "bob"
        }
    },
    "giving": {
        "amount": "0.00",
        "currency": "EUR"
    },
    "goal": null,
    "id": %(user_id)s,
    "kind": "individual",
    "my_tip": "self",
    "npatrons": 1,
    "receiving": {
        "amount": "3.00",
        "currency": "EUR"
    },
    "username": "bob"
});''' % dict(user_id=bob.id, elsewhere_id=bob.get_accounts_elsewhere()['github'].id)
