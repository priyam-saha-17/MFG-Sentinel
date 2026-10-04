USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE NOTIFICATION INTEGRATION MFG_SENTINEL_EMAIL_INT
    TYPE = EMAIL
    ENABLED = TRUE
    DEFAULT_RECIPIENTS = ('impriyamsaha@gmail.com')
    DEFAULT_SUBJECT = 'MFG Sentinel - Critical Machine Failure Alert';



SHOW NOTIFICATION INTEGRATIONS LIKE 'MFG_SENTINEL_EMAIL_INT';



CALL SYSTEM$SEND_EMAIL(
    'MFG_SENTINEL_EMAIL_INT',
    'impriyamsaha@gmail.com',
    'MFG Sentinel - Test Alert',
    'This is a test email from the MFG Sentinel predictive maintenance application.'
);
