/**
 * VetBooking - Script principal
 * Inspirado no Doctoralia
 */

document.addEventListener('DOMContentLoaded', function() {
    // Navegação responsiva
    const navbarToggle = document.querySelector('.navbar-toggle');
    const navMenu = document.querySelector('.nav-links');
    
    if (navbarToggle) {
        navbarToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
            this.classList.toggle('active');
        });
    }
    
    // Validação de formulários
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            const passwordField = form.querySelector('input[type="password"]');
            const confirmPasswordField = form.querySelector('input[id="confirm-password"]');
            
            if (passwordField && confirmPasswordField) {
                if (passwordField.value !== confirmPasswordField.value) {
                    event.preventDefault();
                    alert('As senhas não coincidem. Por favor, verifique.');
                }
            }
        });
    });
    
    // Preview de imagem para upload
    const fileInputs = document.querySelectorAll('.file-input');
    
    fileInputs.forEach(input => {
        input.addEventListener('change', function(event) {
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                const preview = this.parentElement.querySelector('.file-preview');
                
                reader.onload = function(e) {
                    // Limpar o conteúdo atual
                    preview.innerHTML = '';
                    
                    // Criar elemento de imagem
                    const img = document.createElement('img');
                    img.src = e.target.result;
                    preview.appendChild(img);
                };
                
                reader.readAsDataURL(file);
            }
        });
    });
    
    // Animação de scroll suave para links internos
    const internalLinks = document.querySelectorAll('a[href^="#"]');
    
    internalLinks.forEach(link => {
        link.addEventListener('click', function(event) {
            const targetId = this.getAttribute('href');
            if (targetId !== '#') {
                event.preventDefault();
                const targetElement = document.querySelector(targetId);
                if (targetElement) {
                    window.scrollTo({
                        top: targetElement.offsetTop - 80, // Ajuste para o cabeçalho fixo
                        behavior: 'smooth'
                    });
                }
            }
        });
    });
    
    // Efeito de destaque para campos de formulário
    const formInputs = document.querySelectorAll('.form-input, .form-textarea');
    
    formInputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        input.addEventListener('blur', function() {
            this.parentElement.classList.remove('focused');
        });
    });
    
    // Função para formulário em etapas
    window.nextStep = function(currentStep) {
        document.getElementById(`step-${currentStep}`).classList.remove('active');
        document.getElementById(`step-${currentStep + 1}`).classList.add('active');
        
        // Atualizar barra de progresso
        const progressSteps = document.querySelectorAll('.progress-step');
        progressSteps[currentStep].classList.add('active');
    };
    
    window.prevStep = function(currentStep) {
        document.getElementById(`step-${currentStep}`).classList.remove('active');
        document.getElementById(`step-${currentStep - 1}`).classList.add('active');
        
        // Atualizar barra de progresso
        const progressSteps = document.querySelectorAll('.progress-step');
        progressSteps[currentStep - 1].classList.remove('active');
    };
});