/**
 * intelligence.js — Trading Intelligence Learning Engine Frontend
 * Modules: Knowledge Library, PDF Reader, Teach Mode, Learning Memory, Approved Lessons, History & Backups.
 */

(function () {
    'use strict';

    // State
    const state = {
        currentSubtab: 'library',
        categories: ['Footprint Analysis', 'GEX Analysis', 'Volume Profile'],
        documents: [],
        lessons: [],
        currentDocId: null,
        teachPendingResult: null,
        attachedChartBase64: null,
        attachedChartFilename: null,
    };

    // Elements cache
    let el = {};

    function init() {
        cacheElements();
        bindEvents();
        loadCategories();
        loadStats();
        loadDocuments();
        loadLessons();
    }

    function cacheElements() {
        el = {
            subtabBtns: document.querySelectorAll('.intel-tab-btn'),
            subtabContents: document.querySelectorAll('.intel-tab-content'),
            statBadge: document.getElementById('intelStatsBadge'),
            statDocs: document.getElementById('intelStatDocs'),
            statLessons: document.getElementById('intelStatLessons'),

            // Library
            dropZone: document.getElementById('intelDropZone'),
            fileInput: document.getElementById('intelFileInput'),
            categorySelect: document.getElementById('intelCategorySelect'),
            uploadProgress: document.getElementById('intelUploadProgress'),
            uploadProgressBar: document.getElementById('intelProgressBar'),
            uploadStatusText: document.getElementById('intelUploadStatusText'),
            libraryGrid: document.getElementById('intelLibraryGrid'),
            libraryFilterCategory: document.getElementById('intelFilterCategory'),
            btnAddCategory: document.getElementById('intelBtnAddCategory'),

            // PDF Reader
            readerDocSelect: document.getElementById('intelReaderDocSelect'),
            readerDocTitle: document.getElementById('intelReaderDocTitle'),
            readerDocCategory: document.getElementById('intelReaderDocCategory'),
            readerDocSummary: document.getElementById('intelReaderDocSummary'),
            readerConceptsList: document.getElementById('intelReaderConceptsList'),
            readerQaInput: document.getElementById('intelReaderQaInput'),
            readerBtnAsk: document.getElementById('intelReaderBtnAsk'),
            readerQaHistory: document.getElementById('intelReaderQaHistory'),

            // Teach Mode
            teachCategory: document.getElementById('intelTeachCategory'),
            teachInput: document.getElementById('intelTeachInput'),
            teachChartInput: document.getElementById('intelTeachChartInput'),
            teachBtnAttach: document.getElementById('intelTeachBtnAttach'),
            teachAttachedBadge: document.getElementById('intelTeachAttachedBadge'),
            teachBtnAnalyze: document.getElementById('intelTeachBtnAnalyze'),
            teachLoading: document.getElementById('intelTeachLoading'),
            teachResultCard: document.getElementById('intelTeachResultCard'),
            teachResultTitle: document.getElementById('intelTeachResultTitle'),
            teachResultCategory: document.getElementById('intelTeachResultCategory'),
            teachResultUnderstanding: document.getElementById('intelTeachResultUnderstanding'),
            teachResultComparison: document.getElementById('intelTeachResultComparison'),
            teachResultClarifications: document.getElementById('intelTeachResultClarifications'),
            teachResultRules: document.getElementById('intelTeachResultRules'),
            teachResultExamples: document.getElementById('intelTeachResultExamples'),
            teachBtnApprove: document.getElementById('intelTeachBtnApprove'),
            teachBtnRevise: document.getElementById('intelTeachBtnRevise'),

            // Memory
            memorySearchInput: document.getElementById('intelMemorySearch'),
            memoryCategoryFilter: document.getElementById('intelMemoryCategoryFilter'),
            memoryStatusFilter: document.getElementById('intelMemoryStatusFilter'),
            memoryTableBody: document.getElementById('intelMemoryTableBody'),

            // Approved Lessons
            approvedList: document.getElementById('intelApprovedList'),
            approvedCategoryFilter: document.getElementById('intelApprovedCategoryFilter'),

            // History & Backups
            auditLogList: document.getElementById('intelAuditLogList'),
            btnBackup: document.getElementById('intelBtnBackup'),
            btnRestoreFile: document.getElementById('intelRestoreFileInput'),
            tradesList: document.getElementById('intelTradesList'),
            btnLogTrade: document.getElementById('intelBtnLogTrade'),
        };
    }

    function bindEvents() {
        // Subtab navigation
        el.subtabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const subtab = btn.dataset.subtab;
                switchSubtab(subtab);
            });
        });

        // Drop zone file selection
        if (el.dropZone && el.fileInput) {
            el.dropZone.addEventListener('click', () => el.fileInput.click());
            el.dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                el.dropZone.classList.add('drag-over');
            });
            el.dropZone.addEventListener('dragleave', () => el.dropZone.classList.remove('drag-over'));
            el.dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                el.dropZone.classList.remove('drag-over');
                if (e.dataTransfer.files.length > 0) {
                    handleFileUpload(e.dataTransfer.files[0]);
                }
            });
            el.fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    handleFileUpload(e.target.files[0]);
                }
            });
        }

        // Add Category
        if (el.btnAddCategory) {
            el.btnAddCategory.addEventListener('click', async () => {
                const name = prompt('Enter new Knowledge Category:');
                if (name && name.trim()) {
                    await addCategory(name.trim());
                }
            });
        }

        // Library Filter
        if (el.libraryFilterCategory) {
            el.libraryFilterCategory.addEventListener('change', () => {
                loadDocuments(el.libraryFilterCategory.value);
            });
        }

        // PDF Reader document switch
        if (el.readerDocSelect) {
            el.readerDocSelect.addEventListener('change', (e) => {
                loadDocumentDetail(e.target.value);
            });
        }

        // PDF Reader Ask Question
        if (el.readerBtnAsk && el.readerQaInput) {
            el.readerBtnAsk.addEventListener('click', () => askDocumentQuestion());
            el.readerQaInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    askDocumentQuestion();
                }
            });
        }

        // Teach Mode Chart Attach
        if (el.teachBtnAttach && el.teachChartInput) {
            el.teachBtnAttach.addEventListener('click', () => el.teachChartInput.click());
            el.teachChartInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    const file = e.target.files[0];
                    const reader = new FileReader();
                    reader.onload = () => {
                        state.attachedChartBase64 = reader.result;
                        state.attachedChartFilename = file.name;
                        el.teachAttachedBadge.textContent = `📎 ${file.name}`;
                        el.teachAttachedBadge.style.display = 'inline-block';
                    };
                    reader.readAsDataURL(file);
                }
            });
        }

        // Teach Mode Analyze
        if (el.teachBtnAnalyze) {
            el.teachBtnAnalyze.addEventListener('click', () => analyzeTeachingInput());
        }

        // Teach Mode Approve
        if (el.teachBtnApprove) {
            el.teachBtnApprove.addEventListener('click', () => approveTeachResult());
        }

        // Teach Mode Revise
        if (el.teachBtnRevise) {
            el.teachBtnRevise.addEventListener('click', () => {
                el.teachResultCard.style.display = 'none';
                el.teachInput.focus();
            });
        }

        // Learning Memory Filters
        if (el.memorySearchInput) {
            el.memorySearchInput.addEventListener('input', () => filterMemoryTable());
        }
        if (el.memoryCategoryFilter) {
            el.memoryCategoryFilter.addEventListener('change', () => filterMemoryTable());
        }
        if (el.memoryStatusFilter) {
            el.memoryStatusFilter.addEventListener('change', () => filterMemoryTable());
        }

        // Approved Lessons Category Filter
        if (el.approvedCategoryFilter) {
            el.approvedCategoryFilter.addEventListener('change', () => {
                renderApprovedLessons(el.approvedCategoryFilter.value);
            });
        }

        // Database Backup download
        if (el.btnBackup) {
            el.btnBackup.addEventListener('click', () => exportDatabaseBackup());
        }

        // Database Restore upload
        if (el.btnRestoreFile) {
            el.btnRestoreFile.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    importDatabaseBackup(e.target.files[0]);
                }
            });
        }

        // Log trade button
        if (el.btnLogTrade) {
            el.btnLogTrade.addEventListener('click', () => promptLogTrade());
        }
    }

    function switchSubtab(subtabName) {
        state.currentSubtab = subtabName;
        el.subtabBtns.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.subtab === subtabName);
        });
        el.subtabContents.forEach(content => {
            const match = content.id.toLowerCase().includes(subtabName);
            content.style.display = match ? 'flex' : 'none';
            content.classList.toggle('active', match);
        });

        // Trigger on-switch data refreshes
        if (subtabName === 'library') loadDocuments();
        if (subtabName === 'memory') loadLessons();
        if (subtabName === 'approved') loadLessons();
        if (subtabName === 'history') { loadAuditLog(); loadTrades(); }
    }

    // ── API Interactions ─────────────────────────────────────────────────────

    async function loadCategories() {
        try {
            const resp = await fetch('/api/intelligence/categories');
            const data = await resp.json();
            if (data.categories) {
                state.categories = data.categories;
                populateCategoryDropdowns(data.categories);
            }
        } catch (e) {
            console.warn('Could not load categories:', e);
        }
    }

    function populateCategoryDropdowns(cats) {
        const selects = [
            el.categorySelect,
            el.libraryFilterCategory,
            el.teachCategory,
            el.memoryCategoryFilter,
            el.approvedCategoryFilter
        ];

        selects.forEach(sel => {
            if (!sel) return;
            const isFilter = sel.id.toLowerCase().includes('filter');
            const prevVal = sel.value;
            sel.innerHTML = isFilter ? '<option value="">All Categories</option>' : '';
            cats.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c;
                opt.textContent = c;
                sel.appendChild(opt);
            });
            if (prevVal) sel.value = prevVal;
        });
    }

    async function addCategory(name) {
        try {
            const resp = await fetch('/api/intelligence/categories', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name })
            });
            const data = await resp.json();
            if (data.ok) {
                state.categories = data.categories;
                populateCategoryDropdowns(data.categories);
                alert(`Category '${name}' added successfully!`);
            } else {
                alert(data.detail || 'Could not add category');
            }
        } catch (e) {
            alert('Failed to add category: ' + e);
        }
    }

    async function loadStats() {
        try {
            const resp = await fetch('/api/intelligence/stats');
            const data = await resp.json();
            if (el.statDocs) el.statDocs.textContent = `${data.total_documents || 0} Docs`;
            if (el.statLessons) el.statLessons.textContent = `${data.approved_lessons || 0} Approved Lessons`;
        } catch (e) {
            console.warn('Stats fetch error:', e);
        }
    }

    // ── Module 1 & 2: Document Upload & PDF Reader ───────────────────────────

    async function handleFileUpload(file) {
        const cat = el.categorySelect ? el.categorySelect.value : 'Footprint Analysis';
        const formData = new FormData();
        formData.append('file', file);
        formData.append('category', cat);

        if (el.uploadProgress) {
            el.uploadProgress.style.display = 'block';
            el.uploadProgressBar.style.width = '30%';
            el.uploadStatusText.textContent = `Reading & Extracting concepts from '${file.name}' via Neural Intelligence...`;
        }

        try {
            const resp = await fetch('/api/intelligence/upload', {
                method: 'POST',
                body: formData
            });
            const data = await resp.json();

            if (el.uploadProgressBar) el.uploadProgressBar.style.width = '100%';

            if (data.ok) {
                if (el.uploadStatusText) {
                    el.uploadStatusText.textContent = `✓ Extracted ${data.concepts_count} concepts from ${data.document.original_name}!`;
                }
                setTimeout(() => {
                    if (el.uploadProgress) el.uploadProgress.style.display = 'none';
                    if (el.fileInput) el.fileInput.value = '';
                }, 3000);

                await loadDocuments();
                await loadStats();

                // Open in PDF Reader directly
                if (confirm(`Document processed successfully with ${data.concepts_count} extracted concepts. Open in PDF/Doc Reader now?`)) {
                    switchSubtab('reader');
                    loadDocumentDetail(data.document.id);
                }
            } else {
                alert(data.detail || 'Upload failed');
                if (el.uploadProgress) el.uploadProgress.style.display = 'none';
            }
        } catch (e) {
            alert('File processing error: ' + e);
            if (el.uploadProgress) el.uploadProgress.style.display = 'none';
        }
    }

    async function loadDocuments(categoryFilter = '') {
        try {
            const url = categoryFilter
                ? `/api/intelligence/documents?category=${encodeURIComponent(categoryFilter)}`
                : '/api/intelligence/documents';
            const resp = await fetch(url);
            const data = await resp.json();
            state.documents = data.documents || [];
            renderLibraryGrid(state.documents);
            updateReaderDocDropdown(state.documents);
        } catch (e) {
            console.warn('Documents load error:', e);
        }
    }

    function renderLibraryGrid(docs) {
        if (!el.libraryGrid) return;
        el.libraryGrid.innerHTML = '';

        if (docs.length === 0) {
            el.libraryGrid.innerHTML = `
                <div class="intel-empty-card">
                    <span class="intel-empty-icon">📂</span>
                    <div class="intel-empty-title">Knowledge Library is Empty</div>
                    <div class="intel-empty-sub">Upload trading PDFs, screenshots, CSVs or guides above to populate your library.</div>
                </div>
            `;
            return;
        }

        docs.forEach(doc => {
            const card = document.createElement('div');
            card.className = 'intel-doc-card';

            const iconMap = {
                pdf: '📄',
                png: '🖼️',
                jpg: '🖼️',
                jpeg: '🖼️',
                txt: '📝',
                csv: '📊',
                docx: '📑'
            };
            const icon = iconMap[doc.file_type] || '📁';
            const sizeStr = doc.size_bytes < 1024 * 1024
                ? `${(doc.size_bytes / 1024).toFixed(1)} KB`
                : `${(doc.size_bytes / (1024 * 1024)).toFixed(1)} MB`;

            card.innerHTML = `
                <div class="doc-card-header">
                    <span class="doc-icon">${icon}</span>
                    <div class="doc-meta-wrap">
                        <div class="doc-title" title="${esc(doc.original_name)}">${esc(doc.original_name)}</div>
                        <div class="doc-badge-row">
                            <span class="doc-category-badge">${esc(doc.category)}</span>
                            <span class="doc-size-badge">${sizeStr}</span>
                            ${doc.page_count > 1 ? `<span class="doc-pages-badge">${doc.page_count} Pages</span>` : ''}
                        </div>
                    </div>
                </div>
                <div class="doc-summary-preview">${esc(doc.summary || 'Document knowledge cataloged.')}</div>
                <div class="doc-card-actions">
                    <button class="doc-action-btn primary" onclick="window.JARVIS_INTEL.openInReader('${doc.id}')">📖 Open in Reader</button>
                    <button class="doc-action-btn danger" onclick="window.JARVIS_INTEL.deleteDoc('${doc.id}')">🗑️</button>
                </div>
            `;
            el.libraryGrid.appendChild(card);
        });
    }

    function updateReaderDocDropdown(docs) {
        if (!el.readerDocSelect) return;
        const prev = el.readerDocSelect.value;
        el.readerDocSelect.innerHTML = '<option value="">-- Select a Document to Explore --</option>';
        docs.forEach(d => {
            const opt = document.createElement('option');
            opt.value = d.id;
            opt.textContent = `${d.original_name} [${d.category}]`;
            el.readerDocSelect.appendChild(opt);
        });
        if (prev) el.readerDocSelect.value = prev;
    }

    async function loadDocumentDetail(docId) {
        if (!docId) return;
        state.currentDocId = docId;
        if (el.readerDocSelect) el.readerDocSelect.value = docId;

        try {
            const resp = await fetch(`/api/intelligence/document/${docId}`);
            const data = await resp.json();
            const doc = data.document;
            const concepts = data.concepts || [];

            if (el.readerDocTitle) el.readerDocTitle.textContent = doc.original_name;
            if (el.readerDocCategory) el.readerDocCategory.textContent = doc.category;
            if (el.readerDocSummary) el.readerDocSummary.textContent = doc.summary || 'No summary available.';

            renderExtractedConcepts(concepts);
            if (el.readerQaHistory) {
                el.readerQaHistory.innerHTML = `
                    <div class="qa-msg ai">
                        <div class="qa-speaker">🧠 MARK 59</div>
                        <div class="qa-body">I have reviewed <b>${esc(doc.original_name)}</b>. You can ask any question about the rules, examples, or methodologies contained in this document.</div>
                    </div>
                `;
            }
        } catch (e) {
            console.error('Document detail load error:', e);
        }
    }

    function renderExtractedConcepts(concepts) {
        if (!el.readerConceptsList) return;
        el.readerConceptsList.innerHTML = '';

        if (concepts.length === 0) {
            el.readerConceptsList.innerHTML = '<div style="color:var(--text-muted); font-size:12px; padding:10px;">No discrete concepts parsed yet.</div>';
            return;
        }

        concepts.forEach((c, idx) => {
            const cBox = document.createElement('div');
            cBox.className = 'concept-card';

            const rulesHtml = (c.trading_rules && c.trading_rules.length > 0)
                ? `<div class="concept-section-title">📐 Trading Rules:</div>
                   <ul class="concept-bullet-list">
                     ${c.trading_rules.map(r => `<li><b>Rule:</b> ${esc(r)}</li>`).join('')}
                   </ul>`
                : '';

            const examplesHtml = (c.practical_examples && c.practical_examples.length > 0)
                ? `<div class="concept-section-title">💡 Examples & Setups:</div>
                   <ul class="concept-bullet-list">
                     ${c.practical_examples.map(ex => `<li>${esc(ex)}</li>`).join('')}
                   </ul>`
                : '';

            cBox.innerHTML = `
                <div class="concept-header">
                    <span class="concept-num">#${idx + 1}</span>
                    <span class="concept-name">${esc(c.concept_name)}</span>
                    <span class="concept-ref">${esc(c.source_reference || '')}</span>
                </div>
                <div class="concept-explanation">${esc(c.explanation)}</div>
                ${rulesHtml}
                ${examplesHtml}
            `;
            el.readerConceptsList.appendChild(cBox);
        });
    }

    async function askDocumentQuestion() {
        if (!state.currentDocId) {
            alert('Please select a document first.');
            return;
        }
        const q = el.readerQaInput ? el.readerQaInput.value.trim() : '';
        if (!q) return;

        // Append user message
        const uMsg = document.createElement('div');
        uMsg.className = 'qa-msg user';
        uMsg.innerHTML = `<div class="qa-speaker">You</div><div class="qa-body">${esc(q)}</div>`;
        el.readerQaHistory.appendChild(uMsg);
        el.readerQaInput.value = '';
        el.readerQaHistory.scrollTop = el.readerQaHistory.scrollHeight;

        // Append placeholder AI message
        const aiMsg = document.createElement('div');
        aiMsg.className = 'qa-msg ai thinking';
        aiMsg.innerHTML = `<div class="qa-speaker">🧠 MARK 59</div><div class="qa-body">Consulting document and verifying citations...</div>`;
        el.readerQaHistory.appendChild(aiMsg);
        el.readerQaHistory.scrollTop = el.readerQaHistory.scrollHeight;

        try {
            const resp = await fetch(`/api/intelligence/document/${state.currentDocId}/ask`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: q })
            });
            const data = await resp.json();
            aiMsg.classList.remove('thinking');
            aiMsg.querySelector('.qa-body').innerHTML = formatMarkdownText(data.answer);
            el.readerQaHistory.scrollTop = el.readerQaHistory.scrollHeight;
        } catch (e) {
            aiMsg.classList.remove('thinking');
            aiMsg.querySelector('.qa-body').textContent = 'Error processing document question: ' + e;
        }
    }

    // ── Module 3: Teach Mode ─────────────────────────────────────────────────

    async function analyzeTeachingInput() {
        const text = el.teachInput ? el.teachInput.value.trim() : '';
        if (!text) {
            alert('Please write your trading explanation or rule first.');
            return;
        }
        const cat = el.teachCategory ? el.teachCategory.value : 'Footprint Analysis';

        if (el.teachLoading) el.teachLoading.style.display = 'flex';
        if (el.teachResultCard) el.teachResultCard.style.display = 'none';

        try {
            const resp = await fetch('/api/intelligence/teach/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    explanation: text,
                    category: cat,
                    chart_image_base64: state.attachedChartBase64,
                    chart_filename: state.attachedChartFilename,
                })
            });
            const res = await resp.json();
            if (el.teachLoading) el.teachLoading.style.display = 'none';

            state.teachPendingResult = res;
            renderTeachResult(res);
        } catch (e) {
            if (el.teachLoading) el.teachLoading.style.display = 'none';
            alert('Failed to analyze teaching: ' + e);
        }
    }

    function renderTeachResult(res) {
        if (!el.teachResultCard) return;
        el.teachResultTitle.textContent = res.title || 'Institutional Trading Lesson';
        el.teachResultCategory.textContent = res.category;
        el.teachResultUnderstanding.textContent = res.ai_understanding;
        el.teachResultComparison.textContent = res.comparison_notes;

        // Clarifications
        if (res.clarifications_asked && res.clarifications_asked.length > 0) {
            el.teachResultClarifications.style.display = 'block';
            el.teachResultClarifications.innerHTML = `
                <div class="teach-sub-heading">❓ Clarification / Ambiguities:</div>
                <ul>${res.clarifications_asked.map(c => `<li>${esc(c)}</li>`).join('')}</ul>
            `;
        } else {
            el.teachResultClarifications.style.display = 'none';
        }

        // Rules
        if (res.proposed_rules && res.proposed_rules.length > 0) {
            el.teachResultRules.innerHTML = `
                <div class="teach-sub-heading">📋 Actionable Trading Rules:</div>
                <ul>${res.proposed_rules.map(r => `<li><b>Rule:</b> ${esc(r)}</li>`).join('')}</ul>
            `;
        } else {
            el.teachResultRules.innerHTML = '';
        }

        // Examples
        if (res.proposed_examples && res.proposed_examples.length > 0) {
            el.teachResultExamples.innerHTML = `
                <div class="teach-sub-heading">💡 Practical Examples:</div>
                <ul>${res.proposed_examples.map(ex => `<li>${esc(ex)}</li>`).join('')}</ul>
            `;
        } else {
            el.teachResultExamples.innerHTML = '';
        }

        el.teachResultCard.style.display = 'block';
        el.teachResultCard.scrollIntoView({ behavior: 'smooth' });
    }

    async function approveTeachResult() {
        if (!state.teachPendingResult) return;
        const r = state.teachPendingResult;

        try {
            const resp = await fetch('/api/intelligence/teach/approve', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: r.title,
                    category: r.category,
                    user_explanation: r.user_explanation,
                    ai_understanding: r.ai_understanding,
                    trading_rules: r.proposed_rules || [],
                    practical_examples: r.proposed_examples || [],
                    chart_image_path: r.chart_image_path
                })
            });
            const data = await resp.json();
            if (data.ok) {
                alert(`✓ Lesson '${r.title}' APPROVED & saved to Institutional Playbook!`);
                if (el.teachResultCard) el.teachResultCard.style.display = 'none';
                if (el.teachInput) el.teachInput.value = '';
                if (el.teachAttachedBadge) el.teachAttachedBadge.style.display = 'none';
                state.attachedChartBase64 = null;
                state.attachedChartFilename = null;
                state.teachPendingResult = null;

                await loadLessons();
                await loadStats();
            } else {
                alert(data.detail || 'Failed to approve lesson.');
            }
        } catch (e) {
            alert('Approval error: ' + e);
        }
    }

    // ── Module 4 & 5: Learning Memory & Approved Playbook ────────────────────

    async function loadLessons() {
        try {
            const resp = await fetch('/api/intelligence/lessons');
            const data = await resp.json();
            state.lessons = data.lessons || [];
            renderMemoryTable(state.lessons);
            renderApprovedLessons();
        } catch (e) {
            console.warn('Lessons load error:', e);
        }
    }

    function renderMemoryTable(lessons) {
        if (!el.memoryTableBody) return;
        el.memoryTableBody.innerHTML = '';

        if (lessons.length === 0) {
            el.memoryTableBody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:var(--text-muted); padding:20px;">No trading lessons in memory yet. Teach Mark 59 in Teach Mode!</td></tr>';
            return;
        }

        lessons.forEach(l => {
            const tr = document.createElement('tr');
            const statusClass = l.status === 'approved' ? 'badge-approved' : (l.status === 'rejected' ? 'badge-rejected' : 'badge-pending');
            const dateStr = l.approved_at ? l.approved_at.split('T')[0] : l.created_at.split('T')[0];

            tr.innerHTML = `
                <td><b>${esc(l.title)}</b></td>
                <td><span class="cat-pill">${esc(l.category)}</span></td>
                <td><span class="status-pill ${statusClass}">${esc(l.status.toUpperCase())}</span></td>
                <td>v${l.version}.0</td>
                <td>${dateStr}</td>
                <td>
                    ${l.status === 'pending' ? `<button class="tbl-btn approve" onclick="window.JARVIS_INTEL.approveLessonById('${l.id}')">Approve</button>` : ''}
                    <button class="tbl-btn delete" onclick="window.JARVIS_INTEL.deleteLessonById('${l.id}')">Delete</button>
                </td>
            `;
            el.memoryTableBody.appendChild(tr);
        });
    }

    function filterMemoryTable() {
        const query = el.memorySearchInput ? el.memorySearchInput.value.toLowerCase().trim() : '';
        const cat = el.memoryCategoryFilter ? el.memoryCategoryFilter.value : '';
        const st = el.memoryStatusFilter ? el.memoryStatusFilter.value : '';

        const filtered = state.lessons.filter(l => {
            const mText = !query || l.title.toLowerCase().includes(query) || l.ai_understanding.toLowerCase().includes(query) || (l.trading_rules || []).some(r => r.toLowerCase().includes(query));
            const mCat = !cat || l.category === cat;
            const mSt = !st || l.status === st;
            return mText && mCat && mSt;
        });
        renderMemoryTable(filtered);
    }

    function renderApprovedLessons(catFilter = '') {
        if (!el.approvedList) return;
        el.approvedList.innerHTML = '';

        const approved = state.lessons.filter(l => l.status === 'approved' && (!catFilter || l.category === catFilter));

        if (approved.length === 0) {
            el.approvedList.innerHTML = `
                <div class="intel-empty-card">
                    <span class="intel-empty-icon">🛡️</span>
                    <div class="intel-empty-title">No Approved Lessons Yet</div>
                    <div class="intel-empty-sub">Approved lessons form your verified institutional trading playbook. Teach Mark 59 and click Approve to store them here!</div>
                </div>
            `;
            return;
        }

        approved.forEach(l => {
            const card = document.createElement('div');
            card.className = 'playbook-rule-card';

            const rulesList = (l.trading_rules && l.trading_rules.length > 0)
                ? `<div class="pb-section-title">Strict Execution Rules:</div>
                   <ul class="pb-rules-list">
                     ${l.trading_rules.map(r => `<li><b>RULE:</b> ${esc(r)}</li>`).join('')}
                   </ul>`
                : '';

            const examplesList = (l.practical_examples && l.practical_examples.length > 0)
                ? `<div class="pb-section-title">Practical Setup Examples:</div>
                   <ul class="pb-rules-list">
                     ${l.practical_examples.map(ex => `<li>${esc(ex)}</li>`).join('')}
                   </ul>`
                : '';

            card.innerHTML = `
                <div class="pb-card-header">
                    <div class="pb-title-wrap">
                        <span class="pb-title">${esc(l.title)}</span>
                        <span class="pb-version">v${l.version}.0</span>
                    </div>
                    <span class="pb-cat-badge">${esc(l.category)}</span>
                </div>
                <div class="pb-body">
                    <div class="pb-desc"><b>Core Understanding:</b> ${esc(l.ai_understanding)}</div>
                    ${rulesList}
                    ${examplesList}
                </div>
                <div class="pb-footer">
                    <span>Approved: ${l.approved_at ? l.approved_at.split('T')[0] : l.created_at.split('T')[0]}</span>
                    <button class="tbl-btn delete" onclick="window.JARVIS_INTEL.deleteLessonById('${l.id}')">Remove Rule</button>
                </div>
            `;
            el.approvedList.appendChild(card);
        });
    }

    // ── Module 5 & 6: History, Trades, Backup & Restore ──────────────────────

    async function loadAuditLog() {
        try {
            const resp = await fetch('/api/intelligence/history');
            const data = await resp.json();
            const logs = data.audit_log || [];
            if (!el.auditLogList) return;
            el.auditLogList.innerHTML = '';

            if (logs.length === 0) {
                el.auditLogList.innerHTML = '<div style="color:var(--text-muted); font-size:12px;">No activity logged yet.</div>';
                return;
            }

            logs.forEach(log => {
                const item = document.createElement('div');
                item.className = 'audit-log-item';
                const timeStr = log.timestamp.replace('T', ' ').slice(0, 19);
                item.innerHTML = `
                    <span class="audit-time">${timeStr}</span>
                    <span class="audit-badge ${log.action}">${log.action.toUpperCase()}</span>
                    <span class="audit-text"><b>${esc(log.entity_type)}</b> [${esc(log.entity_id.slice(0, 8))}] ${esc(JSON.stringify(log.details))}</span>
                `;
                el.auditLogList.appendChild(item);
            });
        } catch (e) {
            console.warn('Audit log error:', e);
        }
    }

    async function loadTrades() {
        try {
            const resp = await fetch('/api/intelligence/trades');
            const data = await resp.json();
            const trades = data.trades || [];
            if (!el.tradesList) return;
            el.tradesList.innerHTML = '';

            if (trades.length === 0) {
                el.tradesList.innerHTML = '<div style="color:var(--text-muted); font-size:12px; padding:10px;">No trades logged yet in learning architecture.</div>';
                return;
            }

            trades.forEach(t => {
                const box = document.createElement('div');
                box.className = 'trade-journal-card';
                box.innerHTML = `
                    <div style="display:flex; justify-content:space-between; font-weight:600;">
                        <span>${esc(t.symbol)} (${esc(t.direction)}) @ ${t.entry_price}</span>
                        <span class="outcome-${t.outcome}">${t.outcome.toUpperCase()}</span>
                    </div>
                    <div style="font-size:12px; color:var(--text-muted); margin-top:4px;"><b>Why:</b> ${esc(t.why_entered)}</div>
                    ${t.lessons_learned ? `<div style="font-size:12px; color:var(--green); margin-top:4px;"><b>Lesson:</b> ${esc(t.lessons_learned)}</div>` : ''}
                `;
                el.tradesList.appendChild(box);
            });
        } catch (e) {
            console.warn('Trades load error:', e);
        }
    }

    function promptLogTrade() {
        const symbol = prompt('Symbol (e.g. XAUUSDT):', 'XAUUSDT');
        if (!symbol) return;
        const dir = prompt('Direction (BUY / SELL):', 'BUY');
        const price = prompt('Entry Price:', '2850.00');
        const why = prompt('Why entered (Which GEX/Footprint levels?):', 'Absorption at CW0 with positive CVD delta');
        const outcome = prompt('Outcome (win / loss / breakeven):', 'win');
        const lesson = prompt('What did you learn from this outcome?:', 'Waiting for absorption confirmation prevented early stop out.');

        fetch('/api/intelligence/trades', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                symbol: symbol.toUpperCase(),
                direction: dir.toUpperCase(),
                entry_price: parseFloat(price) || 0,
                why_entered: why || '',
                outcome: outcome.toLowerCase() || 'pending',
                lessons_learned: lesson || ''
            })
        }).then(r => r.json()).then(data => {
            if (data.ok) {
                alert('Trade logged into learning memory!');
                loadTrades();
            }
        });
    }

    async function exportDatabaseBackup() {
        try {
            const resp = await fetch('/api/intelligence/backup');
            const data = await resp.json();
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `JARVIS_MARK59_Intelligence_Backup_${new Date().toISOString().split('T')[0]}.json`;
            a.click();
            URL.revokeObjectURL(url);
        } catch (e) {
            alert('Export failed: ' + e);
        }
    }

    async function importDatabaseBackup(file) {
        if (!confirm('Restoring will merge knowledge and lessons from backup into your database. Proceed?')) return;
        const reader = new FileReader();
        reader.onload = async () => {
            try {
                const json = JSON.parse(reader.result);
                const resp = await fetch('/api/intelligence/restore', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(json)
                });
                const data = await resp.json();
                if (data.ok) {
                    alert('Database restored successfully!');
                    loadStats();
                    loadDocuments();
                    loadLessons();
                    loadCategories();
                } else {
                    alert(data.detail || 'Restore failed.');
                }
            } catch (err) {
                alert('Invalid JSON file: ' + err);
            }
        };
        reader.readAsText(file);
    }

    // ── Helper Utilities ─────────────────────────────────────────────────────

    function esc(s) {
        if (!s) return '';
        return String(s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function formatMarkdownText(md) {
        if (!md) return '';
        return md
            .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
            .replace(/\*(.*?)\*/g, '<i>$1</i>')
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/\n\n/g, '<br><br>')
            .replace(/\n- /g, '<br>• ');
    }

    // Global hook for inline onclick buttons
    window.JARVIS_INTEL = {
        openInReader: (id) => {
            switchSubtab('reader');
            loadDocumentDetail(id);
        },
        deleteDoc: async (id) => {
            if (confirm('Delete this document and all its extracted concepts?')) {
                await fetch(`/api/intelligence/document/${id}`, { method: 'DELETE' });
                loadDocuments();
                loadStats();
            }
        },
        approveLessonById: async (id) => {
            await fetch(`/api/intelligence/lesson/${id}/approve`, { method: 'POST' });
            loadLessons();
            loadStats();
        },
        deleteLessonById: async (id) => {
            if (confirm('Delete this lesson from memory?')) {
                await fetch(`/api/intelligence/lesson/${id}`, { method: 'DELETE' });
                loadLessons();
                loadStats();
            }
        },
        refresh: () => {
            loadCategories();
            loadStats();
            loadDocuments();
            loadLessons();
        }
    };

    // Auto-init when DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
