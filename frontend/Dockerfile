# Stage 1: Build the React application
FROM node:18-alpine AS build

WORKDIR /app

COPY package.json package-lock.json* ./
# Use npm install instead of npm ci to avoid lock file version conflicts
RUN npm install
COPY . ./
RUN npm run build

# Stage 2: Serve the application using Nginx
FROM nginx:stable-alpine

# Copy the build output from the build stage
COPY --from=build /app/build /usr/share/nginx/html

# Copy Nginx configs and the startup script
COPY nginx.dev.conf /etc/nginx/nginx.dev.conf
COPY nginx.prod.conf /etc/nginx/nginx.prod.conf
COPY start.sh /start.sh

# Make the startup script executable
RUN chmod +x /start.sh

# Expose port 80
EXPOSE 80

# Run the startup script
CMD ["/start.sh"]