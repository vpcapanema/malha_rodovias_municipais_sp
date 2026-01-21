// ============================================
// main.js - Script de interatividade
// Estudo Malha Viária Vicinal - SP
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    
    // ========================================
    // 1. NAVEGAÇÃO ATIVA
    // ========================================
    highlightActiveNav();
    
    // ========================================
    // 2. SMOOTH SCROLL
    // ========================================
    enableSmoothScroll();
    
    // ========================================
    // 3. MENU RESPONSIVO
    // ========================================
    setupResponsiveMenu();
    
    // ========================================
    // 4. SORTING TABELAS
    // ========================================
    enableTableSorting();
    
    // ========================================
    // 5. PROGRESS BAR ANIMAÇÃO
    // ========================================
    animateProgressBars();
    
    // ========================================
    // 6. TOOLTIPS
    // ========================================
    initializeTooltips();
    
    // ========================================
    // 7. BACK TO TOP BUTTON
    // ========================================
    setupBackToTop();
});

// ============================================
// FUNÇÕES DE NAVEGAÇÃO
// ============================================

/**
 * Destaca o link de navegação da página atual
 */
function highlightActiveNav() {
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href && href.includes(currentPage)) {
            link.classList.add('active');
        }
    });
}

/**
 * Habilita scroll suave para âncoras
 */
function enableSmoothScroll() {
    const anchors = document.querySelectorAll('a[href^="#"]');
    
    anchors.forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

/**
 * Menu hamburguer para mobile
 */
function setupResponsiveMenu() {
    // Criar botão se não existir
    const nav = document.querySelector('.nav');
    if (!nav) return;
    
    let menuBtn = document.querySelector('.menu-toggle');
    if (!menuBtn) {
        menuBtn = document.createElement('button');
        menuBtn.className = 'menu-toggle';
        menuBtn.innerHTML = '<span></span><span></span><span></span>';
        menuBtn.setAttribute('aria-label', 'Toggle menu');
        nav.insertBefore(menuBtn, nav.firstChild);
    }
    
    const navList = document.querySelector('.nav-list');
    
    menuBtn.addEventListener('click', function() {
        navList.classList.toggle('nav-active');
        this.classList.toggle('active');
    });
    
    // Fechar menu ao clicar em link
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            navList.classList.remove('nav-active');
            menuBtn.classList.remove('active');
        });
    });
}

// ============================================
// FUNÇÕES DE TABELAS
// ============================================

/**
 * Adiciona funcionalidade de ordenação às tabelas
 */
function enableTableSorting() {
    const tables = document.querySelectorAll('table');
    
    tables.forEach(table => {
        const headers = table.querySelectorAll('thead th');
        
        headers.forEach((header, index) => {
            // Adicionar cursor pointer
            header.style.cursor = 'pointer';
            header.style.userSelect = 'none';
            
            // Adicionar indicador visual
            const sortIndicator = document.createElement('span');
            sortIndicator.className = 'sort-indicator';
            sortIndicator.innerHTML = ' ↕';
            header.appendChild(sortIndicator);
            
            header.addEventListener('click', () => {
                sortTable(table, index);
                updateSortIndicators(header, sortIndicator);
            });
        });
    });
}

/**
 * Ordena tabela por coluna
 */
function sortTable(table, columnIndex) {
    const tbody = table.querySelector('tbody');
    if (!tbody) return;
    
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const currentSort = table.dataset.sortColumn;
    const currentOrder = table.dataset.sortOrder || 'asc';
    
    // Determinar ordem
    let newOrder = 'asc';
    if (currentSort === columnIndex.toString() && currentOrder === 'asc') {
        newOrder = 'desc';
    }
    
    // Ordenar
    rows.sort((a, b) => {
        const aValue = getCellValue(a, columnIndex);
        const bValue = getCellValue(b, columnIndex);
        
        // Tentar comparação numérica
        const aNum = parseFloat(aValue.replace(/[^\d.-]/g, ''));
        const bNum = parseFloat(bValue.replace(/[^\d.-]/g, ''));
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return newOrder === 'asc' ? aNum - bNum : bNum - aNum;
        }
        
        // Comparação texto
        return newOrder === 'asc' 
            ? aValue.localeCompare(bValue)
            : bValue.localeCompare(aValue);
    });
    
    // Reordenar DOM
    rows.forEach(row => tbody.appendChild(row));
    
    // Salvar estado
    table.dataset.sortColumn = columnIndex;
    table.dataset.sortOrder = newOrder;
}

/**
 * Obtém valor da célula para ordenação
 */
function getCellValue(row, columnIndex) {
    const cell = row.querySelectorAll('td')[columnIndex];
    return cell ? cell.textContent.trim() : '';
}

/**
 * Atualiza indicadores visuais de ordenação
 */
function updateSortIndicators(activeHeader, activeIndicator) {
    // Reset todos
    document.querySelectorAll('.sort-indicator').forEach(ind => {
        ind.innerHTML = ' ↕';
        ind.style.opacity = '0.5';
    });
    
    // Destacar ativo
    const table = activeHeader.closest('table');
    const order = table.dataset.sortOrder;
    activeIndicator.innerHTML = order === 'asc' ? ' ↑' : ' ↓';
    activeIndicator.style.opacity = '1';
}

// ============================================
// ANIMAÇÕES
// ============================================

/**
 * Anima barras de progresso quando visíveis
 */
function animateProgressBars() {
    const progressBars = document.querySelectorAll('.progress-fill');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const fill = entry.target;
                const targetWidth = fill.style.width;
                
                // Reset e animate
                fill.style.width = '0';
                setTimeout(() => {
                    fill.style.transition = 'width 1.5s ease-out';
                    fill.style.width = targetWidth;
                }, 100);
                
                observer.unobserve(fill);
            }
        });
    }, { threshold: 0.5 });
    
    progressBars.forEach(bar => observer.observe(bar));
}

/**
 * Anima números quando visíveis (count-up)
 */
function animateNumbers() {
    const statValues = document.querySelectorAll('.stat-value');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const element = entry.target;
                const targetText = element.textContent;
                const targetNum = parseFloat(targetText.replace(/[^\d.-]/g, ''));
                
                if (!isNaN(targetNum)) {
                    animateValue(element, 0, targetNum, 1500, targetText);
                }
                
                observer.unobserve(element);
            }
        });
    }, { threshold: 0.5 });
    
    statValues.forEach(stat => observer.observe(stat));
}

/**
 * Anima valor numérico (count-up effect)
 */
function animateValue(element, start, end, duration, originalText) {
    const startTime = performance.now();
    const suffix = originalText.replace(/[\d.-]/g, '').trim();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        const current = start + (end - start) * easeOutCubic(progress);
        element.textContent = formatNumber(current) + (suffix ? ' ' + suffix : '');
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

/**
 * Easing function
 */
function easeOutCubic(t) {
    return 1 - Math.pow(1 - t, 3);
}

/**
 * Formata número para exibição
 */
function formatNumber(num) {
    if (num >= 1000) {
        return Math.round(num).toLocaleString('pt-BR');
    }
    return num.toFixed(num % 1 !== 0 ? 1 : 0);
}

// ============================================
// TOOLTIPS
// ============================================

/**
 * Inicializa tooltips para elementos com atributo data-tooltip
 */
function initializeTooltips() {
    const elements = document.querySelectorAll('[data-tooltip]');
    
    elements.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

/**
 * Mostra tooltip
 */
function showTooltip(e) {
    const text = e.target.getAttribute('data-tooltip');
    if (!text) return;
    
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = text;
    tooltip.id = 'active-tooltip';
    
    document.body.appendChild(tooltip);
    
    // Posicionar
    const rect = e.target.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 10 + 'px';
    
    // Fade in
    setTimeout(() => tooltip.style.opacity = '1', 10);
}

/**
 * Esconde tooltip
 */
function hideTooltip() {
    const tooltip = document.getElementById('active-tooltip');
    if (tooltip) {
        tooltip.style.opacity = '0';
        setTimeout(() => tooltip.remove(), 200);
    }
}

// ============================================
// BACK TO TOP
// ============================================

/**
 * Botão voltar ao topo
 */
function setupBackToTop() {
    // Criar botão
    const btn = document.createElement('button');
    btn.className = 'back-to-top';
    btn.innerHTML = '↑';
    btn.setAttribute('aria-label', 'Voltar ao topo');
    document.body.appendChild(btn);
    
    // Mostrar/esconder baseado em scroll
    window.addEventListener('scroll', () => {
        if (window.pageYOffset > 300) {
            btn.classList.add('visible');
        } else {
            btn.classList.remove('visible');
        }
    });
    
    // Ação de click
    btn.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// ============================================
// UTILITÁRIOS
// ============================================

/**
 * Debounce function para otimização
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Detecta se é dispositivo móvel
 */
function isMobile() {
    return window.innerWidth < 768;
}

/**
 * Log de desenvolvimento (remover em produção)
 */
function devLog(...args) {
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        console.log('[DEV]', ...args);
    }
}

// ============================================
// EXPORT PARA USO EXTERNO (se necessário)
// ============================================
window.EstudoVicinais = {
    sortTable,
    animateProgressBars,
    formatNumber
};
