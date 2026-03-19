ARG PHP_VERSION="8.5"
ARG ALPINE_VERSION="3.23"
ARG CADDY_VERSION="2.11"

FROM caddy:${CADDY_VERSION}-alpine AS caddy-upstream

FROM php:${PHP_VERSION}-fpm-alpine${ALPINE_VERSION} AS builder
ARG DEBUG
ARG USE_EXTRA="false"

ARG COMPOSER_VERSION="2.9.4"

RUN apk --update-cache add \
            git \
            patch \
            gettext-dev \
            jpeg-dev \
            libpng-dev \
            zlib-dev \
            icu-dev \
            libzip-dev \
            freetype-dev \
            libxml2-dev

RUN if [ "$USE_EXTRA" = "true" ]; then \
        apk add --no-cache $PHPIZE_DEPS imagemagick-dev libtool postgresql-dev && \
        pecl install imagick && \
        docker-php-ext-enable imagick && \
        docker-php-ext-configure gd --with-jpeg --with-freetype && \
        docker-php-ext-install -j$(nproc) gd pdo_mysql pdo_pgsql exif zip bcmath xml simplexml; \
    else \
        docker-php-ext-configure gd --with-jpeg && \
        docker-php-ext-install -j$(nproc) gd bcmath; \
    fi
RUN docker-php-ext-install -j$(nproc) gettext intl

WORKDIR /tmp

RUN curl https://getcomposer.org/installer | php -- --version ${COMPOSER_VERSION}

RUN rm -rf /var/www && mkdir /var/www
COPY --from=p2-rep2 . /var/www

WORKDIR /var/www

RUN /tmp/composer.phar install
RUN rm -rf `find . -name '.git*' -o -name 'composer.*'`

COPY patch /tmp
RUN patch --no-backup-if-mismatch -p1 < /tmp/p2-php.patch

RUN mv conf conf.orig && ln -s /ext/conf conf
RUN mv data data.orig && ln -s /ext/data data
RUN ln -s /ext/rep2/ic rep2/ic

COPY --from=2chproxy.pl 2chproxy.pl .
RUN chmod 755 2chproxy.pl
RUN mv 2chproxy.pl /usr/local/bin/


FROM php:${PHP_VERSION}-fpm-alpine${ALPINE_VERSION}
LABEL org.opencontainers.image.authors="Abe Masahiro <pen@thcomp.org>" \
    org.opencontainers.image.source="https://github.com/pen/docker-rep2"
ARG DEBUG
ARG USE_EXTRA="false"

ARG REPO_HASH
ARG REPO_LOG
ARG REP2_HASH
ARG REP2_LOG
ARG RUN_ID
ARG RUN_NUMBER
ENV VER_REPO_HASH=$REPO_HASH
ENV VER_REPO_LOG=$REPO_LOG
ENV VER_REP2_HASH=$REP2_HASH
ENV VER_REP2_LOG=$REP2_LOG
ENV VER_RUN_ID=$RUN_ID
ENV VER_RUN_NUMBER=$RUN_NUMBER

RUN apk --no-cache add \
            su-exec \
            gettext \
            libintl \
            libjpeg \
            libpng \
            perl-http-daemon \
            perl-lwp-useragent-determined \
            perl-yaml-tiny \
            perl-io-socket-ssl \
            perl-lwp-protocol-https \
            ca-certificates \
            zlib \
            tzdata \
            icu-libs

RUN if [ "$USE_EXTRA" = "true" ]; then \
        apk --no-cache add imagemagick libpq libzip freetype libxml2; \
    fi

COPY --from=caddy-upstream /usr/bin/caddy /usr/bin/caddy

RUN if [ "$DEBUG" = "on" ]; then \
    apk --no-cache add tshark; \
    apk --no-cache add  --virtual .build-deps $PHPIZE_DEPS linux-headers \
    && pecl install xdebug \
    && docker-php-ext-enable xdebug \
    && apk del .build-deps; \
    fi

COPY --from=builder /usr/local /usr/local
COPY --from=builder /var/www   /var/www
COPY rootfs /

VOLUME /ext
EXPOSE 443

CMD ["/etc/rc.entry"]
