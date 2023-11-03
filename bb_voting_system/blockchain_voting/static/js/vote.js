
// Генерация ключей
document.getElementById('generate-keys-button').addEventListener('click', () => {
    fetch('/generate-keys', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('public-key').textContent = data.public_key;
        document.getElementById('private-key').textContent = data.private_key;
        checkFields(); // Проверьте поля после получения ключей
    })
    .catch(error => {
        console.error('Error:', error);
    });
});


// Получите элементы полей выбора опции и кнопки "Голосовать"
const voteOption = document.getElementById('vote-option');
const voteButton = document.getElementById('vote-button');

// Добавьте слушатель события изменения поля выбора опции
voteOption.addEventListener('change', () => {
    checkFields(); // Проверьте поля после каждого изменения
});

// Функция для проверки полей и активации/деактивации кнопки "Голосовать"
function checkFields() {
    if (voteOption.value && hasGeneratedKeys()) {
        voteButton.removeAttribute('disabled');
    } else {
        voteButton.setAttribute('disabled', 'disabled');
    }
}

// Функция для проверки, были ли сгенерированы ключи
function hasGeneratedKeys() {
    const publicKey = document.getElementById('public-key').textContent;
    const privateKey = document.getElementById('private-key').textContent;
    return publicKey && privateKey;
}
