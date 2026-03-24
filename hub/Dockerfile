FROM node:22-alpine AS build
WORKDIR /app
RUN corepack enable
COPY .yarnrc.yml package.json yarn.lock ./
RUN yarn install --immutable
COPY . .
RUN yarn build

FROM nginx:alpine
RUN mkdir -p /tmp/nginx-client-body /tmp/nginx-proxy /tmp/nginx-fastcgi /tmp/nginx-uwsgi /tmp/nginx-scgi \
    && chown -R nginx:nginx /tmp/nginx-client-body /tmp/nginx-proxy /tmp/nginx-fastcgi /tmp/nginx-uwsgi /tmp/nginx-scgi
COPY nginx.main.conf /etc/nginx/nginx.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
