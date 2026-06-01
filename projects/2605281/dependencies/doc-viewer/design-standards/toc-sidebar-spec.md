# TOC Sidebar Specification — 目录导航侧边栏规范

> 本规范定义可折叠侧边栏目录导航组件，从 h2/h3 自动提取生成锚点目录，支持 PC/平板/移动端三端适配。

---

## 1. 功能概述

### 1.1 核心功能
- **自动提取目录**：从页面的 h2/h3 标题自动生成目录树
- **滚动高亮**：使用 IntersectionObserver 监听滚动，高亮当前章节
- **平滑滚动**：点击目录项平滑滚动到对应锚点
- **响应式适配**：PC 端侧边浮动，平板端浮动按钮，移动端全屏抽屉
- **打印隐藏**：打印时自动隐藏导航组件

### 1.2 适用场景
- 长文档（> 1500 字）
- 多章节报告（≥ 3 个 h2 标题）
- 结构化内容页

---

## 2. 视觉风格

### 2.1 颜色变量适配

目录导航使用各模板的 CSS 变量，确保与主色保持一致：

```css
/* 主色变量（各模板不同，直接引用） */
.toc-sidebar {
  --toc-bg: var(--bg-primary, #fff);
  --toc-border: var(--border-color, #e5e7eb);
  --toc-text: var(--text-primary, #1f2937);
  --toc-text-muted: var(--text-secondary, #6b7280);
  --toc-accent: var(--accent-color, #2563eb);
  --toc-hover: var(--hover-bg, #f3f4f6);
}
```

### 2.2 层级视觉
- **h2 级别**：主目录项，左侧边框高亮色条
- **h3 级别**：子目录项，缩进 12px，灰色文本

---

## 3. 组件结构

### 3.1 HTML 结构

```html
<!-- 目录侧边栏容器 -->
<nav class="toc-sidebar" id="toc-sidebar">
  <!-- 折叠按钮（默认显示） -->
  <button class="toc-toggle" id="toc-toggle" aria-label="切换目录">
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
      <line x1="3" y1="12" x2="21" y2="12" stroke-width="2"/>
      <line x1="3" y1="6" x2="21" y2="6" stroke-width="2"/>
      <line x1="3" y1="18" x2="21" y2="18" stroke-width="2"/>
    </svg>
  </button>

  <!-- 目录内容（默认隐藏） -->
  <div class="toc-content" id="toc-content" style="display: none;">
    <div class="toc-header">
      <span class="toc-title">目录</span>
      <button class="toc-close" id="toc-close" aria-label="关闭目录">×</button>
    </div>
    <ul class="toc-list" id="toc-list">
      <!-- 动态生成目录项 -->
    </ul>
  </div>
</nav>

<!-- 移动端遮罩 -->
<div class="toc-overlay" id="toc-overlay" style="display: none;"></div>
```

---

## 4. CSS 样式

### 4.1 基础样式

```css
/* 目录侧边栏容器 */
.toc-sidebar {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 100;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

/* 折叠按钮 */
.toc-toggle {
  width: 44px;
  height: 44px;
  background: var(--toc-bg);
  border: 1px solid var(--toc-border);
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
}

.toc-toggle:hover {
  background: var(--toc-hover);
  transform: scale(1.05);
}

.toc-toggle:active {
  transform: scale(0.95);
}

/* 目录内容容器 */
.toc-content {
  position: absolute;
  top: 0;
  right: 0;
  width: 240px;
  max-height: calc(100vh - 40px);
  background: var(--toc-bg);
  border: 1px solid var(--toc-border);
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  animation: slideIn 0.2s ease;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateX(10px); }
  to { opacity: 1; transform: translateX(0); }
}

/* 目录头部 */
.toc-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--toc-border);
  background: var(--toc-hover);
}

.toc-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--toc-text);
}

.toc-close {
  width: 28px;
  height: 28px;
  border: none;
  background: none;
  font-size: 18px;
  color: var(--toc-text-muted);
  cursor: pointer;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.toc-close:hover {
  background: var(--toc-hover);
  color: var(--toc-text);
}

/* 目录列表 */
.toc-list {
  list-style: none;
  padding: 8px;
  margin: 0;
  overflow-y: auto;
  flex: 1;
}

.toc-list::-webkit-scrollbar {
  width: 4px;
}

.toc-list::-webkit-scrollbar-thumb {
  background: var(--toc-border);
  border-radius: 2px;
}

/* 目录项 */
.toc-item {
  margin: 2px 0;
}

.toc-link {
  display: block;
  padding: 8px 10px;
  font-size: 13px;
  color: var(--toc-text);
  text-decoration: none;
  border-radius: 4px;
  transition: all 0.15s ease;
  border-left: 3px solid transparent;
}

.toc-link:hover {
  background: var(--toc-hover);
}

.toc-link.active {
  background: var(--toc-hover);
  border-left-color: var(--toc-accent);
  color: var(--toc-accent);
  font-weight: 500;
}

/* h3 子目录项 */
.toc-item.h3 > .toc-link {
  padding-left: 22px;
  font-size: 12px;
  color: var(--toc-text-muted);
}
```

### 4.2 PC 端样式（> 1024px）

```css
@media screen and (min-width: 1025px) {
  .toc-sidebar {
    position: fixed;
    top: 40px;
    right: 40px;
    width: 240px;
  }

  .toc-content {
    position: static;
    width: 100%;
    max-height: calc(100vh - 80px);
  }

  .toc-toggle {
    display: none; /* PC 端默认展开，隐藏按钮 */
  }

  .toc-content {
    display: flex !important; /* 强制显示 */
  }

  .toc-header {
    padding: 12px 12px;
  }

  .toc-close {
    display: none; /* PC 端不需要关闭按钮 */
  }
}
```

### 4.3 平板端样式（769px ~ 1024px）

```css
@media screen and (min-width: 769px) and (max-width: 1024px) {
  .toc-sidebar {
    top: 16px;
    right: 16px;
  }

  .toc-content {
    width: 200px;
  }
}
```

### 4.4 移动端样式（≤ 768px）

```css
@media screen and (max-width: 768px) {
  .toc-sidebar {
    top: auto;
    bottom: 20px;
    right: 20px;
  }

  .toc-content {
    position: fixed;
    top: 0;
    right: 0;
    width: 280px;
    max-width: 85vw;
    height: 100vh;
    max-height: 100vh;
    border-radius: 0;
    border: none;
    box-shadow: -4px 0 16px rgba(0, 0, 0, 0.2);
    animation: slideInRight 0.25s ease;
  }

  @keyframes slideInRight {
    from { transform: translateX(100%); }
    to { transform: translateX(0); }
  }

  .toc-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.5);
    z-index: 99;
    display: none;
  }

  .toc-overlay.show {
    display: block;
  }

  .toc-close {
    display: flex; /* 移动端显示关闭按钮 */
  }
}
```

### 4.5 打印样式

```css
@media print {
  .toc-sidebar,
  .toc-overlay {
    display: none !important;
  }
}
```

---

## 5. JavaScript 功能

### 5.1 完整脚本

```html
<script>
(function() {
  'use strict';

  // 配置
  const CONFIG = {
    sidebarId: 'toc-sidebar',
    toggleId: 'toc-toggle',
    contentId: 'toc-content',
    listId: 'toc-list',
    closeId: 'toc-close',
    overlayId: 'toc-overlay',
    minHeadings: 3, // 最少 3 个 h2 才显示目录
    scrollOffset: 80 // 滚动偏移量（避开固定头部）
  };

  // DOM 元素
  const sidebar = document.getElementById(CONFIG.sidebarId);
  const toggleBtn = document.getElementById(CONFIG.toggleId);
  const content = document.getElementById(CONFIG.contentId);
  const list = document.getElementById(CONFIG.listId);
  const closeBtn = document.getElementById(CONFIG.closeId);
  const overlay = document.getElementById(CONFIG.overlayId);

  // 提取标题
  function extractHeadings() {
    const headings = document.querySelectorAll('.page-wrap h2, .page-wrap h3');
    if (headings.length < CONFIG.minHeadings) {
      sidebar.style.display = 'none';
      return;
    }

    // 确保标题有 ID
    headings.forEach((heading, index) => {
      if (!heading.id) {
        heading.id = `heading-${index}`;
      }
    });

    return headings;
  }

  // 生成目录树
  function buildTOC(headings) {
    list.innerHTML = '';
    let currentH2Item = null;

    headings.forEach(heading => {
      const item = document.createElement('li');
      item.className = `toc-item ${heading.tagName.toLowerCase()}`;

      const link = document.createElement('a');
      link.href = `#${heading.id}`;
      link.textContent = heading.textContent;
      link.className = 'toc-link';
      link.dataset.target = heading.id;

      link.addEventListener('click', (e) => {
        e.preventDefault();
        const target = document.getElementById(heading.id);
        if (target) {
          const offset = CONFIG.scrollOffset;
          const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - offset;
          window.scrollTo({
            top: targetPosition,
            behavior: 'smooth'
          });

          // 移动端：点击后关闭目录
          if (window.innerWidth <= 768) {
            closeSidebar();
          }
        }
      });

      item.appendChild(link);
      list.appendChild(item);
    });
  }

  // 切换目录显示/隐藏
  function toggleSidebar() {
    const isHidden = content.style.display === 'none' || !content.style.display;
    content.style.display = isHidden ? 'flex' : 'none';

    // 移动端：显示遮罩
    if (window.innerWidth <= 768 && isHidden) {
      overlay.classList.add('show');
    }
  }

  // 关闭目录（移动端）
  function closeSidebar() {
    content.style.display = 'none';
    overlay.classList.remove('show');
  }

  // 滚动高亮当前章节
  function setupScrollSpy() {
    const headings = Array.from(document.querySelectorAll('.page-wrap h2, .page-wrap h3'));
    const tocLinks = Array.from(document.querySelectorAll('.toc-link'));

    if (headings.length === 0 || tocLinks.length === 0) return;

    const observerOptions = {
      rootMargin: '-100px 0px -80% 0px',
      threshold: 0
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const id = entry.target.id;
          tocLinks.forEach(link => {
            link.classList.remove('active');
            if (link.dataset.target === id) {
              link.classList.add('active');
            }
          });
        }
      });
    }, observerOptions);

    headings.forEach(heading => observer.observe(heading));
  }

  // 事件绑定
  function bindEvents() {
    toggleBtn.addEventListener('click', toggleSidebar);
    closeBtn.addEventListener('click', closeSidebar);
    overlay.addEventListener('click', closeSidebar);

    // ESC 键关闭（移动端）
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && window.innerWidth <= 768) {
        closeSidebar();
      }
    });
  }

  // 初始化
  function init() {
    const headings = extractHeadings();
    if (headings && headings.length >= CONFIG.minHeadings) {
      buildTOC(headings);
      bindEvents();
      setupScrollSpy();

      // PC 端：默认展开
      if (window.innerWidth > 1024) {
        content.style.display = 'flex';
      }
    }
  }

  // DOM 加载完成后初始化
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
</script>
```

---

## 6. 使用指南

### 6.1 内联到 HTML

将上述代码复制到 HTML 文件中：

1. **HTML 结构**：粘贴到 `<body>` 结束标签前
2. **CSS 样式**：粘贴到 `<style>` 标签中
3. **JavaScript**：粘贴到 `</body>` 前的 `<script>` 标签中

### 6.2 自定义配置

如需调整配置，修改 JS 中的 `CONFIG` 对象：

```javascript
const CONFIG = {
  minHeadings: 3,      // 最少标题数（默认 3 个 h2）
  scrollOffset: 80,    // 滚动偏移量（避开固定头部）
  sidebarId: 'toc-sidebar',
  // ...
};
```

### 6.3 与模板主色集成

确保模板定义了以下 CSS 变量：

```css
:root {
  --bg-primary: #ffffff;
  --border-color: #e5e7eb;
  --text-primary: #1f2937;
  --text-secondary: #6b7280;
  --accent-color: #2563eb;
  --hover-bg: #f3f4f6;
}
```

目录导航会自动引用这些变量。

---

## 7. 风格适配建议

### 7.1 专用型风格（03、11、12）
- **适用场景**：结构化报告、评估文档
- **推荐开启**：✅ 长文档（> 1500 字）
- **默认行为**：按需开启（根据内容长度）

### 7.2 系列型风格（02）
- **适用场景**：多变体报告系统
- **推荐开启**：根据变体决定
  - 02-A（封面）：❌ 不开启
  - 02-B（章节页）：✅ 开启
  - 02-C（正文页）：✅ 开启

### 7.3 通用型风格（01、04、05、06、07、08、09、10）
- **适用场景**：通用内容页
- **推荐开启**：✅ 默认开启（除超短内容）

---

## 8. Do's and Don'ts

**Do's：**
- ✅ 使用 CSS 变量适配模板主色
- ✅ 移动端点击目录项后自动关闭
- ✅ 打印时自动隐藏导航
- ✅ 平滑滚动带偏移量（避开固定头部）
- ✅ 至少 3 个 h2 标题才显示目录

**Don'ts：**
- ❌ 硬编码颜色值（不使用 var()）
- ❌ 移动端不提供关闭按钮
- ❌ 打印时不隐藏导航
- ❌ 滚动高亮不准确（未使用 IntersectionObserver）
- ❌ PC 端默认折叠（应默认展开）

---

## 9. 兼容性

- **浏览器支持**：Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **移动端**：iOS Safari 14+, Android Chrome 90+
- **关键 API**：IntersectionObserver（ widely supported ）

---

## 10. 性能优化

### 10.1 滚动性能
- 使用 `IntersectionObserver` 而非 scroll 事件监听
- `rootMargin` 优化监听范围

### 10.2 渲染性能
- 目录项使用 `transform` 动画（GPU 加速）
- 滚动高亮切换 class（避免直接操作 style）

### 10.3 加载性能
- 脚本放在 `</body>` 前（不阻塞渲染）
- DOM 加载完成后初始化（`DOMContentLoaded`）
