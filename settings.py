from os import environ

SESSION_CONFIGS = [
    dict(
        name='smith1962_induced',
        display_name='Smith 1962: induced demand/supply (buyers vs sellers)',
        app_sequence=['singleAsset'],
        num_demo_participants=4,
        market_time=180,
        randomise_types=False,
        short_selling=False,
        margin_buying=False,
        num_trial_rounds=0,
        smith_mode=True,
        smith_units_per_trader=4,
        smith_initial_cash_buyer=500,
        smith_initial_cash_seller=0,
        smith_payoff_scale=0.2,
        smith_buyer_values=[[110, 95, 80, 65], [105, 90, 75, 60], [100, 85, 70, 55]],
        smith_seller_costs=[[25, 40, 55, 70], [30, 45, 60, 75], [35, 50, 65, 80]],
        fixed_asset_value=0,
        thanks_message='Takk for deltakelsen! Vennligst gå tilbake til eksperimentlederen for utbetaling.',
    ),
]

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00, participation_fee=0.00, doc=""
)

ROOMS = [
    dict(
        name='markedseksperiment',
        display_name='Markedseksperiment',
        # participant_label_file='_rooms/participants.txt',  # optional: pre-set participant labels
    ),
]

PARTICIPANT_FIELDS = ['roleID', 'isObserver', 'isParticipating', 'informed']
SESSION_FIELDS = ['numParticipants']

# ISO-639 code
# for example: de, fr, ja, ko, zh-hans
LANGUAGE_CODE = 'en'

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'EUR'
USE_POINTS = False

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
SECRET_KEY = '776841529'

DEMO_PAGE_INTRO_HTML = """ """

INSTALLED_APPS = ['otree']
#DEBUG = False
#AUTH_LEVEL = DEMO
