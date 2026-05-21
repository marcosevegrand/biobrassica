FROM owasp/modsecurity-crs:nginx-alpine

USER root

RUN mkdir -p /opt/biobrassica/templates && \
    printf '%s\n' \
    'SecRuleEngine On' \
    'SecRequestBodyAccess On' \
    'SecResponseBodyAccess On' \
    'SecAuditEngine RelevantOnly' \
    'SecAuditLog /var/log/modsec_audit.log' \
    'SecDebugLog /dev/null' \
    'SecDebugLogLevel 0' \
    'SecPcreMatchLimit 100000' \
    'SecPcreMatchLimitRecursion 100000' \
    'SecRequestBodyLimit 13107200' \
    'SecRequestBodyNoFilesLimit 131072' \
    'SecResponseBodyLimit 1048576' \
    'Include /opt/owasp-crs/crs-setup.conf' \
    'Include /opt/owasp-crs/rules/*.conf' \
    > /etc/nginx/modsecurity/main.conf

COPY conf.d/ /opt/biobrassica/templates/
COPY nginx.conf /etc/nginx/nginx.conf
COPY render-nginx-config.sh /opt/biobrassica/render-nginx-config.sh

RUN chmod +x /opt/biobrassica/render-nginx-config.sh && \
    mkdir -p /var/log/modsecurity && \
    chown nginx:nginx /var/log/modsecurity
