FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci --legacy-peer-deps

COPY . .
RUN npx ng build --configuration=production

FROM nginx:alpine

COPY --from=build /app/dist/evaluacion-quinquenal-front/browser /usr/share/nginx/html

COPY nginx-main.conf /etc/nginx/nginx.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf

RUN chown -R nginx:nginx /usr/share/nginx/html /etc/nginx/conf.d /var/cache/nginx /var/log/nginx

EXPOSE 80

USER nginx
CMD ["nginx", "-g", "daemon off;"]
