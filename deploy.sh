#!/bin/bash

# Выходить немедленно, если команда завершается с ошибкой.
set -e

# --- Вспомогательные функции ---
print_info() {
    echo -e "\033[34m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[32m[SUCCESS]\033[0m $1"
}

# --- 1. Проверка зависимостей (Docker, Docker Compose) ---
print_info "Проверка наличия Docker и Docker Compose..."
if ! command -v docker &> /dev/null; then
    print_info "Docker не найден. Установка Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm get-docker.sh
    # Добавление текущего пользователя в группу docker
    sudo usermod -aG docker $USER
    print_success "Docker установлен. Возможно, потребуется перезайти в систему, чтобы изменения группы вступили в силу."
else
    print_success "Docker уже установлен."
fi

if ! command -v docker-compose &> /dev/null; then
    print_info "Docker Compose не найден. Установка Docker Compose..."
    LATEST_COMPOSE=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
    sudo curl -L "https://github.com/docker/compose/releases/download/${LATEST_COMPOSE}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    print_success "Docker Compose установлен."
else
    print_success "Docker Compose уже установлен."
fi

# --- 2. Сборка и запуск проекта ---
print_info "Сборка Docker-образов. Это может занять некоторое время..."
docker-compose build --no-cache

print_info "Запуск всех сервисов в фоновом режиме..."
docker-compose up -d

print_success "Проект успешно развернут!"
print_info "Бэкенд должен быть доступен по адресу http://<IP_ВАШЕГО_СЕРВЕРА>:8002"
print_info "Фронтенд админки должен быть доступен по адресу http://<IP_ВАШЕГО_СЕРВЕРА>:5173"
echo "Пожалуйста, убедитесь, что эти порты открыты в брандмауэре вашего сервера."

print_info "Чтобы войти в админку, используйте следующие данные (если потребуется):"
print_info "Логин: admin"
print_info "Пароль: admin123"
