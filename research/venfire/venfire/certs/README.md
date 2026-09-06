# Apple public PKI root

`AppleIncRootCertificate.cer` is Apple's unmodified public root certificate,
downloaded on 2026-09-06 through certificate-verified HTTPS from
https://www.apple.com/appleca/AppleIncRootCertificate.cer, linked by Apple's
official PKI directory https://www.apple.com/certificateauthority/.

SHA-256: `b0b1730ecbc7ff4505142c49f1295e6eda6bcaed7e2c68c5be91b5a11001f024`.

The TSS HTTPS client checks this digest and loads the certificate into its own
SSL context. Certificate chains, hostname, and validity dates remain checked.
Redirects are rejected before being followed. No operating-system trust store
is modified. This is a public certificate, not a private signing key or an IMG4
ticket. Its presence cannot sign firmware or replace guest secure-boot checks.
