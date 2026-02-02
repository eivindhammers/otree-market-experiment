from os import environ

SESSION_CONFIGS = [
    dict(
        name='market_experiment',
        display_name="Market Experiment",
        app_sequence=['market_experiment'],
        num_demo_participants=12,
    ),
]

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00,
    participation_fee=0.00,
    doc="",
)

PARTICIPANT_FIELDS = ['role', 'private_value', 'trade_price', 'profit']
SESSION_FIELDS = ['supply_schedule', 'demand_schedule', 'equilibrium_price', 'equilibrium_quantity']

# ISO-639 code
LANGUAGE_CODE = 'en'

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'USD'
USE_POINTS = True

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD', 'admin')

DEMO_PAGE_INTRO_HTML = """
<h2>Market Experiment</h2>
<p>
This experiment demonstrates how decentralized decisions with private information
can lead to market equilibrium. Participants are assigned roles as buyers or sellers
with private values/costs and trade in a call market.
</p>
"""

SECRET_KEY = environ.get('OTREE_SECRET_KEY', '3985672894576')

# if an app is included in SESSION_CONFIGS, you don't need to list it here
INSTALLED_APPS = ['otree']

ROOMS = [
    dict(
        name='econ_class',
        display_name='Economics Class',
    ),
]
