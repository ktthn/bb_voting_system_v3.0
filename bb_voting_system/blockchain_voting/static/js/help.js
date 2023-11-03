// Функция для валидации формы обратной связи
function validateForm() {
    const emailInput = document.getElementById('email');
    const messageInput = document.getElementById('message');
    const errorContainer = document.getElementById('error-message');

    // Проверяем, что email и сообщение заполнены
    if (emailInput.value.trim() === '' || messageInput.value.trim() === '') {
        errorContainer.textContent = 'Пожалуйста, заполните все поля';
        return false;
    }

    // Дополнительная валидация email (простейший вариант)
    const emailPattern = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$/;
    if (!emailPattern.test(emailInput.value)) {
        errorContainer.textContent = 'Пожалуйста, введите корректный email';
        return false;
    }

    errorContainer.textContent = ''; // Очищаем сообщение об ошибке
    return true;
}

// Функция для обработки отправки формы
function handleSubmit(event) {
    event.preventDefault(); // Предотвращаем стандартное поведение формы

    if (validateForm()) {
        // Здесь вы можете добавить код для отправки данных формы на сервер
        // В этом примере мы показываем уведомление и очищаем поля формы
        const notification = document.getElementById('notification');
        notification.style.display = 'block';

        // Очистка полей формы
        document.getElementById('email').value = '';
        document.getElementById('message').value = '';

        // Можете также добавить автоматическое скрытие уведомления через некоторое время
        setTimeout(() => {
            notification.style.display = 'none';
        }, 3000); // Скрывать уведомление через 3 секунды (3000 миллисекунд)
    }
}

// Добавьте обработчик события для формы
const contactForm = document.getElementById('contact-form');
contactForm.addEventListener('submit', handleSubmit);
