FROM nginx:alpine

RUN apk add --no-cache \
    nginx-mod-http-modsecurity \
    modsecurity \
    wget \
    tar

RUN mkdir -p /opt/owasp-crs && \
    wget -qO - https://github.com/coreruleset/coreruleset/archive/refs/tags/v4.13.0.tar.gz | \
    tar xz -C /opt/owasp-crs --strip-components=1

RUN cp /opt/owasp-crs/crs-setup.conf.example /opt/owasp-crs/crs-setup.conf

RUN mkdir -p /etc/nginx/modsecurity && \
    printf 'SecRuleEngine On\nSecRequestBodyAccess On\nSecResponseBodyAccess On\nSecAuditEngine RelevantOnly\nSecAuditLog /var/log/modsec_audit.log\nSecDebugLog /var/log/modsec_debug.log\nSecDebugLogLevel 0\nInclude /opt/owasp-crs/crs-setup.conf\nInclude /opt/owasp-crs/rules/*.conf\n' > /etc/nginx/modsecurity/main.conf

COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d/ /opt/biobrassica/templates/
COPY render-nginx-config.sh /opt/biobrassica/render-nginx-config.sh

RUN chmod +x /opt/biobrassica/render-nginx-config.sh
