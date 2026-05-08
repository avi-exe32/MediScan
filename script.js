
        const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
            ? 'http://localhost:5000'
            : '';
        let currentReportContext = null;

        function showToast(type, message) {
            const container = document.getElementById('toast-container');
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            let icon = type === 'success' ? '✓' : type === 'error' ? '✕' : '!';
            toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
            container.appendChild(toast);
            setTimeout(() => {
                toast.classList.add('fade-out');
                setTimeout(() => toast.remove(), 300);
            }, 4000);
        }

        const options = { year: 'numeric', month: 'short', day: 'numeric' };
        document.getElementById('current-date').innerText = new Date().toLocaleDateString('en-US', options);

        function showPage(pageId) {
            const current = document.querySelector('.page:not(.hidden)');
            const next = document.getElementById('page-' + pageId);

            if (current && current.id !== 'page-' + pageId) {
                current.style.opacity = '0';
                setTimeout(() => {
                    current.classList.add('hidden');
                    next.classList.remove('hidden');
                    next.style.opacity = '0';
                    window.scrollTo({ top: 0, behavior: 'smooth' });

                    // Force reflow
                    void next.offsetWidth;

                    next.style.opacity = '1';
                }, 300);
            } else {
                document.querySelectorAll('.page').forEach(p => p.classList.add('hidden'));
                next.classList.remove('hidden');
                next.style.opacity = '1';
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        }

        // Chat Panel Toggle
        function toggleChatPanel() {
            const panel = document.getElementById('chat-panel');
            const btn = document.getElementById('chat-toggle-btn');
            const isOpen = panel.classList.contains('open');

            if (isOpen) {
                panel.classList.remove('open');
                btn.classList.remove('active');
                panel.style.width = ''; // Remove inline width to allow CSS transition back to 0
            } else {
                panel.classList.add('open');
                btn.classList.add('active');
                setTimeout(() => document.getElementById('chat-input').focus(), 350);
            }
        }

        // Resizable chat panel
        const resizeHandle = document.getElementById('chat-resize-handle');
        const chatPanel = document.getElementById('chat-panel');
        let isResizing = false;
        resizeHandle.addEventListener('mousedown', (e) => {
            isResizing = true;
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
            chatPanel.style.transition = 'none';
        });
        document.addEventListener('mousemove', (e) => {
            if (!isResizing) return;
            const newWidth = window.innerWidth - e.clientX;
            if (newWidth > 240 && newWidth < 600) {
                chatPanel.style.width = newWidth + 'px';
            }
        });
        document.addEventListener('mouseup', () => {
            if (isResizing) {
                chatPanel.style.transition = '';
            }
            isResizing = false;
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        });

        let currentStep = 1;
        const resultsPlaceholder = document.getElementById('results-placeholder');
        const reportContainer = document.getElementById('report-container');

        let currentMainScanFile = null;
        let currentPdfFile = null;
        let currentExtraFile = null;

        function goToStep(step) {
            document.querySelector('.input-panel').style.display = 'flex';
            document.querySelector('.results-panel').style.display = 'none';
            document.querySelector('.app-body').classList.remove('split-screen-mode');

            document.querySelectorAll('.wizard-step-content').forEach(el => el.classList.remove('active'));
            document.getElementById('step-' + step + '-content').classList.add('active');

            for (let i = 1; i <= 4; i++) {
                const nav = document.getElementById('nav-step-' + i);
                const circle = document.getElementById('nav-circle-' + i);
                if (i < step) { nav.classList.add('completed'); nav.classList.remove('active'); circle.innerHTML = "✓"; }
                else if (i === step) { nav.classList.add('active'); nav.classList.remove('completed'); circle.innerHTML = i; }
                else { nav.classList.remove('active', 'completed'); circle.innerHTML = i; }
                if (i < 4) {
                    const lineFill = document.getElementById('line-fill-' + i);
                    if (i < step) lineFill.style.width = '100%'; else lineFill.style.width = '0%';
                }
            }
            currentStep = step;
        }

        let intakeMessageCount = 0;
        let triageDataGlobal = null;

        async function sendIntakeMessage(text) {
            const msg = text || document.getElementById('intake-input').value.trim();
            if (!msg) return;
            
            document.getElementById('intake-input').value = '';
            document.getElementById('suggestion-chips').style.display = 'none';
            
            const chatBox = document.getElementById('intake-chat-container');
            
            // Add user msg
            const userDiv = document.createElement('div');
            userDiv.className = 'msg user';
            userDiv.innerText = msg;
            chatBox.appendChild(userDiv);
            chatBox.scrollTop = chatBox.scrollHeight;
            
            intakeMessageCount++;
            
            // Show typing
            const typingDiv = document.createElement('div');
            typingDiv.className = 'msg ai';
            typingDiv.id = 'intake-typing';
            typingDiv.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
            chatBox.appendChild(typingDiv);
            chatBox.scrollTop = chatBox.scrollHeight;
            
            try {
                // Collect all messages for context
                const msgs = Array.from(chatBox.querySelectorAll('.msg')).map(el => el.innerText).join('\n');
                
                const response = await fetch(`${API_BASE}/triage`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ symptoms: msgs })
                });
                const data = await response.json();
                
                typingDiv.remove();
                
                if (data.success) {
                    triageDataGlobal = data;
                    document.getElementById('btn-proceed-upload').classList.remove('hidden');
                    
                    if (intakeMessageCount < 2 && data.follow_up_questions && data.follow_up_questions.length > 0) {
                        const aiDiv = document.createElement('div');
                        aiDiv.className = 'msg ai';
                        aiDiv.innerText = data.follow_up_questions[0];
                        chatBox.appendChild(aiDiv);
                        chatBox.scrollTop = chatBox.scrollHeight;
                    } else {
                        // Max 2 messages reached, or no follow ups
                        proceedToUploads();
                    }
                } else {
                    const errDiv = document.createElement('div');
                    errDiv.className = 'msg ai';
                    errDiv.style.color = 'var(--danger)';
                    errDiv.innerText = 'Analysis failed: ' + data.error;
                    chatBox.appendChild(errDiv);
                }
            } catch (err) {
                typingDiv.remove();
                const errDiv = document.createElement('div');
                errDiv.className = 'msg ai';
                errDiv.style.color = 'var(--danger)';
                errDiv.innerText = 'Connection failed: ' + err.message;
                chatBox.appendChild(errDiv);
            }
        }

        function proceedToUploads() {
            if (!triageDataGlobal) return;
            const requiredFiles = triageDataGlobal.required_files || [];
            
            document.getElementById('upload-zone-A').style.display = 'none';
            document.getElementById('upload-zone-B').style.display = 'none';
            
            if (requiredFiles.includes('blood_report_pdf')) {
                document.getElementById('triage-doc-sub').innerText = "Based on your symptoms, we need a Pathology or Blood Work report.";
                document.getElementById('upload-zone-A').style.display = 'block';
            } else if (requiredFiles.includes('imaging_scan')) {
                document.getElementById('triage-doc-sub').innerText = "Based on your symptoms, we need an Imaging Scan (X-Ray, MRI, or CT).";
                document.getElementById('image-upload-title').innerText = "Upload Imaging Scan";
                document.getElementById('upload-zone-B').style.display = 'block';
            } else if (requiredFiles.includes('physical_photo')) {
                document.getElementById('triage-doc-sub').innerText = "Based on your symptoms, we need a Physical Photo of the affected area.";
                document.getElementById('image-upload-title').innerText = "Upload Physical Photo";
                document.getElementById('upload-zone-B').style.display = 'block';
            } else {
                document.getElementById('triage-doc-sub').innerText = "Based on your symptoms, please upload any relevant documentation.";
                document.getElementById('image-upload-title').innerText = "Upload Document";
                document.getElementById('upload-zone-B').style.display = 'block';
            }
            
            goToStep(2);
        }

        function enableTreatmentMode() {
            document.querySelector('.app-body').classList.add('split-screen-mode');
            const chatPanel = document.getElementById('chat-panel');
            chatPanel.classList.add('open');
            
            // Add initial treatment message
            addMessage("I have reviewed your clinical report. What questions do you have about the diagnosis, or would you like to discuss potential treatment and next steps?", 'ai');
            
            // Focus chat
            setTimeout(() => document.getElementById('chat-input').focus(), 350);
        }

        function setSegment(groupId, btn) {
            document.querySelectorAll('#' + groupId + ' .segment-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        }

        function setCard(groupId, btn) {
            document.querySelectorAll('#' + groupId + ' .card-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        }

        const mainScanInput = document.getElementById('main-scan-input');
        const mainScanZone = document.getElementById('main-scan-zone');
        mainScanZone.addEventListener('dragover', (e) => { e.preventDefault(); mainScanZone.classList.add('dragover'); });
        mainScanZone.addEventListener('dragleave', () => { mainScanZone.classList.remove('dragover'); });
        mainScanZone.addEventListener('drop', (e) => { e.preventDefault(); mainScanZone.classList.remove('dragover'); if (e.dataTransfer.files[0]) handleMainScan(e.dataTransfer.files[0]); });
        mainScanInput.addEventListener('change', (e) => { if (e.target.files[0]) handleMainScan(e.target.files[0]); });

        function handleMainScan(file) {
            if (!file.type.startsWith('image/')) return alert("Please upload a valid image file.");
            currentMainScanFile = file;
            const reader = new FileReader();
            reader.onload = (e) => {
                document.getElementById('main-scan-image').src = e.target.result;
                document.getElementById('main-scan-info').innerText = `${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
                document.getElementById('main-scan-idle').style.display = 'none';
                document.getElementById('main-scan-preview-container').style.display = 'block';
                mainScanZone.classList.add('uploaded');
                const nextBtn = document.getElementById('btn-next-1');
                nextBtn.disabled = false; nextBtn.style.opacity = '1'; nextBtn.style.cursor = 'pointer';
            };
            reader.readAsDataURL(file);
        }

        function removeMainScan() {
            mainScanInput.value = "";
            currentMainScanFile = null;
            document.getElementById('main-scan-idle').style.display = 'block';
            document.getElementById('main-scan-preview-container').style.display = 'none';
            mainScanZone.classList.remove('uploaded');
            const nextBtn = document.getElementById('btn-next-1');
            nextBtn.disabled = true; nextBtn.style.opacity = '0.45'; nextBtn.style.cursor = 'not-allowed';
        }

        const pdfInput = document.getElementById('pdf-input');
        const pdfZone = document.getElementById('pdf-zone');
        pdfZone.addEventListener('dragover', (e) => { e.preventDefault(); pdfZone.classList.add('dragover'); });
        pdfZone.addEventListener('dragleave', () => { pdfZone.classList.remove('dragover'); });
        pdfZone.addEventListener('drop', (e) => { e.preventDefault(); pdfZone.classList.remove('dragover'); if (e.dataTransfer.files[0]) handlePdf(e.dataTransfer.files[0]); });
        pdfInput.addEventListener('change', (e) => { if (e.target.files[0]) handlePdf(e.target.files[0]); });

        function handlePdf(file) {
            if (file.type !== 'application/pdf') return alert('Please upload a PDF file.');
            currentPdfFile = file;
            document.getElementById('pdf-info').innerText = file.name;
            document.getElementById('pdf-idle').style.display = 'none';
            document.getElementById('pdf-preview').style.display = 'block';
            pdfZone.classList.add('uploaded');
        }
        function removePdf() {
            pdfInput.value = ""; currentPdfFile = null;
            document.getElementById('pdf-idle').style.display = 'block';
            document.getElementById('pdf-preview').style.display = 'none';
            pdfZone.classList.remove('uploaded');
        }

        const extraInput = document.getElementById('extra-input');
        const extraZone = document.getElementById('extra-zone');
        extraZone.addEventListener('dragover', (e) => { e.preventDefault(); extraZone.classList.add('dragover'); });
        extraZone.addEventListener('dragleave', () => { extraZone.classList.remove('dragover'); });
        extraZone.addEventListener('drop', (e) => { e.preventDefault(); extraZone.classList.remove('dragover'); if (e.dataTransfer.files[0]) handleExtra(e.dataTransfer.files[0]); });
        extraInput.addEventListener('change', (e) => { if (e.target.files[0]) handleExtra(e.target.files[0]); });

        function handleExtra(file) {
            if (!file.type.startsWith('image/')) return alert('Please upload an image.');
            currentExtraFile = file;
            const reader = new FileReader();
            reader.onload = (e) => {
                document.getElementById('extra-image').src = e.target.result;
                document.getElementById('extra-idle').style.display = 'none';
                document.getElementById('extra-preview').style.display = 'block';
                extraZone.classList.add('uploaded');
            };
            reader.readAsDataURL(file);
        }
        function removeExtra() {
            extraInput.value = ""; currentExtraFile = null;
            document.getElementById('extra-idle').style.display = 'block';
            document.getElementById('extra-preview').style.display = 'none';
            extraZone.classList.remove('uploaded');
        }

        function setStepActive(id, text) {
            const step = document.getElementById(id);
            step.classList.add('active');
            step.querySelector('.step-indicator').innerHTML = `<span class="loading-spinner"></span>`;
            document.getElementById(id + '-text').innerHTML = text;
        }

        function setStepDone(id, text) {
            const step = document.getElementById(id);
            step.classList.remove('active');
            step.classList.add('done');
            step.querySelector('.step-indicator').innerHTML = "✓";
            document.getElementById(id + '-text').innerText = text;
        }

        async function startAnalysis() {
            if (!currentMainScanFile && !currentPdfFile) {
                alert('Please upload the required documentation first');
                return;
            }

            const nameInput = document.getElementById('pat-name');
            const ageInput = document.getElementById('pat-age');
            let valid = true;
            if (!nameInput.value) { nameInput.style.borderColor = 'var(--danger)'; valid = false; }
            else { nameInput.style.borderColor = ''; }
            if (!ageInput.value) { ageInput.style.borderColor = 'var(--danger)'; valid = false; }
            else { ageInput.style.borderColor = ''; }
            if (!valid) return;

            goToStep(3);

            const nameVal = nameInput.value;
            const ageVal = ageInput.value;
            const genderVal = document.getElementById('pat-gender-select').value;
            const bloodVal = document.getElementById('pat-blood').value;
            // Scan type and region are no longer in UI, leaving blank or omitting
            const scanTypeVal = "";
            const regionVal = "";
            const conditionsVal = document.getElementById('pat-conditions').value;
            const chatBox = document.getElementById('intake-chat-container');
            const symptomsVal = chatBox ? Array.from(chatBox.querySelectorAll('.msg')).map(el => el.innerText).join('\n') : '';
            const toggles = document.querySelectorAll('.toggle-switch');
            const smokingVal = toggles[0].classList.contains('active') ? 'Yes' : 'No';
            const alcoholVal = toggles[1].classList.contains('active') ? 'Yes' : 'No';
            const familyVal = toggles[2].classList.contains('active') ? 'Yes' : 'No';

            const runBtn = document.getElementById('run-analysis-btn');
            runBtn.disabled = true;
            runBtn.innerHTML = 'Analyzing...';
            runBtn.style.opacity = '0.7';

            document.querySelectorAll('input, select, textarea, .segment-btn, .card-btn, .toggle-switch').forEach(el => {
                if (el.tagName === 'DIV' || el.tagName === 'BUTTON') el.style.pointerEvents = 'none';
                else el.disabled = true;
            });

            document.querySelectorAll('.tracker-step').forEach(s => {
                s.classList.remove('active', 'done');
                s.querySelector('.step-indicator').innerHTML = s.id.split('-')[1];
            });
            document.getElementById('step-1-agent-text').innerText = "Waiting...";
            document.getElementById('step-2-agent-text').innerText = "Waiting...";
            document.getElementById('step-3-agent-text').innerText = "Waiting...";
            document.getElementById('analysis-done-msg').classList.add('hidden');
            document.getElementById('report-container').classList.add('hidden');
            document.getElementById('results-placeholder').classList.remove('hidden');

            setStepActive('step-1-agent', "Analyzing image on AMD MI300X GPU using Qwen2-VL-7B-Instruct...");

            const formData = new FormData();
            if (currentMainScanFile) {
                formData.append('scan_image', currentMainScanFile);
            } else if (currentPdfFile) {
                formData.append('scan_image', currentPdfFile);
            }
            if (nameVal) formData.append('patient_name', nameVal);
            if (ageVal) formData.append('age', ageVal);
            if (genderVal) formData.append('gender', genderVal);
            if (bloodVal !== 'Unknown') formData.append('blood_type', bloodVal);
            if (scanTypeVal) formData.append('scan_type', scanTypeVal);
            if (regionVal) formData.append('body_region', regionVal);
            if (conditionsVal) formData.append('known_conditions', conditionsVal);
            if (symptomsVal) formData.append('symptoms', symptomsVal);
            formData.append('smoking', smokingVal);
            formData.append('alcohol', alcoholVal);
            formData.append('family_history', familyVal);

            try {
                const response = await fetch(`${API_BASE}/analyze`, {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();

                if (data.success) {
                    setStepDone('step-1-agent', "Agent 1 Complete — Visual features extracted via Qwen-VL on AMD MI300X");
                    setStepActive('step-2-agent', "Generating clinical report using Gemini 2.0 Flash...");

                    setTimeout(() => {
                        setStepDone('step-2-agent', "Agent 2 Complete — Clinical report generated");
                        setStepActive('step-3-agent', "Cross-checking report consistency...");

                        setTimeout(() => {
                            setStepDone('step-3-agent', `Agent 3 Complete — Report validated. Reliability: ${data.validation?.reliability_score || 0}/10`);
                            document.getElementById('analysis-done-msg').classList.remove('hidden');

                            const nav3 = document.getElementById('nav-step-3');
                            nav3.classList.add('completed'); nav3.classList.remove('active');
                            document.getElementById('nav-circle-3').innerHTML = "✓";

                            const nav4 = document.getElementById('nav-step-4');
                            nav4.classList.add('completed'); nav4.classList.remove('active');
                            document.getElementById('nav-circle-4').innerHTML = "✓";

                            populateReport(data);
                            currentReportContext = JSON.stringify(data.report);
                            showToast('success', 'Analysis complete');
                        }, 600);
                    }, 800);

                } else {
                    throw new Error(data.error || "Analysis failed");
                }
            } catch (err) {
                showToast('error', `Analysis failed: ${err.message}`);
                document.querySelectorAll('.tracker-step').forEach(s => s.classList.remove('active'));
                document.getElementById('step-1-agent-text').innerText = "Failed";
            } finally {
                runBtn.disabled = false;
                runBtn.innerHTML = 'Run Analysis';
                runBtn.style.opacity = '1';
                document.querySelectorAll('input, select, textarea, .segment-btn, .card-btn, .toggle-switch').forEach(el => {
                    if (el.tagName === 'DIV' || el.tagName === 'BUTTON') el.style.pointerEvents = 'all';
                    else el.disabled = false;
                });
            }
        }

        function populateReport(data) {
            const r = data.report || {};
            const v = data.validation || {};
            const p = data.patient || {};

            document.getElementById('rep-name').innerText = p.patient_name || '--';
            document.getElementById('rep-age').innerText = p.age || '--';
            document.getElementById('rep-gender').innerText = p.gender || '--';
            document.getElementById('rep-blood').innerText = p.blood_type || '--';
            document.getElementById('rep-smoking').innerText = p.smoking || '--';
            document.getElementById('rep-alcohol').innerText = p.alcohol || '--';
            document.getElementById('rep-family').innerText = p.family_history || '--';

            document.getElementById('rep-image-type').innerText = `Image: ${r.image_type || '--'}`;
            document.getElementById('rep-body-region').innerText = `Region: ${r.body_region || '--'}`;
            document.getElementById('rep-image-quality').innerText = `Quality: ${r.image_quality || '--'}`;

            const riskObj = r.cancer_risk || {};
            const riskScoreTarget = riskObj.risk_score || 0;
            document.getElementById('risk-level-badge').innerText = riskObj.risk_level ? riskObj.risk_level.toUpperCase() : '--';
            document.getElementById('risk-stage-badge').innerText = riskObj.stage ? `STAGE: ${riskObj.stage.toUpperCase()}` : '--';
            document.getElementById('risk-suspected-type').innerText = riskObj.suspected_type || '--';
            document.getElementById('risk-reasoning').innerText = riskObj.reasoning || '--';

            const lvl = (riskObj.risk_level || '').toLowerCase();
            const badgeLvl = document.getElementById('risk-level-badge');
            if (lvl.includes('high') || lvl.includes('critical')) { badgeLvl.className = 'rbadge rbadge-danger'; }
            else if (lvl.includes('moderate')) { badgeLvl.className = 'rbadge rbadge-warning'; }
            else { badgeLvl.className = 'rbadge rbadge-success'; }

            const findingsHtml = (r.findings || []).map((f, i) => `
            <div class="finding-card">
                <b>${i + 1}. ${f.category || 'Observation'}:</b> ${f.description || ''}
                <span style="opacity: 0.6; font-size: 0.8rem; margin-left: 8px;">(${f.severity || 'Unknown'})</span>
            </div>
        `).join('');
            document.getElementById('findings-container').innerHTML = findingsHtml || '<p style="color:var(--text-3)">No specific findings reported.</p>';

            const conditionsHtml = (r.conditions || []).map(c => {
                let color = 'var(--accent)'; let confWidth = '30%';
                if (c.confidence === 'high') { color = 'var(--danger)'; confWidth = '85%'; }
                else if (c.confidence === 'medium') { color = 'var(--warning)'; confWidth = '60%'; }
                return `
            <div class="condition-card">
                <div class="condition-name">${c.name || 'Unknown Condition'}</div>
                <div class="confidence-bar"><div class="confidence-fill" style="width: ${confWidth}; background: ${color};"></div></div>
                <div class="condition-note"><b>${c.confidence ? c.confidence.toUpperCase() : ''} Confidence.</b> ${c.reasoning || ''}</div>
            </div>`;
            }).join('');
            document.getElementById('conditions-container').innerHTML = conditionsHtml || '<p style="color:var(--text-3)">No differential diagnosis available.</p>';

            const stepsHtml = (r.next_steps || []).map((ns, i) => {
                let urgClass = 'urgency-routine';
                const urg = (ns.urgency || '').toLowerCase();
                if (urg === 'urgent' || urg === 'immediate') urgClass = 'urgency-urgent';
                else if (urg === 'soon') urgClass = 'urgency-soon';
                return `
            <div class="action-card">
                <div class="action-num">${i + 1}</div>
                <div class="action-body">
                    <div class="action-name">${ns.action || ''}</div>
                    <div class="action-reason">${ns.reason || ''}</div>
                </div>
                <span class="urgency-badge ${urgClass}">${ns.urgency || 'Routine'}</span>
            </div>`;
            }).join('');
            document.getElementById('next-steps-container').innerHTML = stepsHtml || '<p style="color:var(--text-3)">No next steps recommended.</p>';

            document.getElementById('validator-score-text').innerText = `Reliability: ${v.reliability_score || 0}/10`;
            document.getElementById('validator-bar-fill').style.width = `${(v.reliability_score || 0) * 10}%`;

            const vVerdict = (v.verdict || '').toLowerCase();
            const vBadge = document.getElementById('validator-verdict');
            vBadge.innerText = `VERDICT: ${v.verdict || '--'}`;
            if (vVerdict.includes('pass') && !vVerdict.includes('warning')) { vBadge.className = 'vchip rbadge-success'; }
            else if (vVerdict.includes('fail')) { vBadge.className = 'vchip rbadge-danger'; }
            else { vBadge.className = 'vchip rbadge-warning'; }

            document.getElementById('validator-note').innerText = v.validator_note || '--';

            let flagsHtml = `<span class="vchip ${vBadge.className}">${vBadge.innerText}</span>`;
            flagsHtml += `<span class="vchip" style="background: var(--bg); border-color: var(--border); color: var(--text-2);">${v.validator_note || '--'}</span>`;
            (v.flags || []).forEach(f => {
                flagsHtml += `<span class="vchip rbadge-warning">${f}</span>`;
            });
            document.getElementById('validator-flags-container').innerHTML = flagsHtml;

            showReport(riskScoreTarget);
        }

        function showReport(targetScore) {
            document.querySelector('.input-panel').style.display = 'none';
            document.querySelector('.results-panel').style.display = 'block';

            resultsPlaceholder.classList.add('hidden');
            reportContainer.classList.remove('hidden');

            setTimeout(() => {
                const gaugeFill = document.getElementById('risk-gauge');
                const scoreText = document.getElementById('risk-score');
                let currentPercent = 0;
                const animate = () => {
                    if (currentPercent <= targetScore) {
                        gaugeFill.style.background = `conic-gradient(var(--danger) ${currentPercent}%, transparent 0%)`;
                        scoreText.innerText = Math.floor(currentPercent);
                        currentPercent += 1.5;
                        requestAnimationFrame(animate);
                    } else {
                        scoreText.innerText = targetScore;
                        gaugeFill.style.background = `conic-gradient(var(--danger) ${targetScore}%, transparent 0%)`;
                    }
                };
                requestAnimationFrame(animate);
            }, 600);

            setTimeout(() => {
                reportContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 100);
        }

        function resetWizard() { goToStep(1); }

        // CHATBOT
        const chatBody = document.getElementById('chat-body');
        const chatInput = document.getElementById('chat-input');

        function toggleChat() { toggleChatPanel(); }

        function handleChatKey(e) {
            if (e.key === 'Enter') sendMessage();
        }

        async function sendMessage() {
            const text = chatInput.value.trim();
            if (!text) return;
            addMessage(text, 'user');
            chatInput.value = '';

            const typingDiv = document.createElement('div');
            typingDiv.className = 'msg ai';
            typingDiv.id = 'typing-indicator';
            typingDiv.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
            chatBody.appendChild(typingDiv);
            chatBody.scrollTop = chatBody.scrollHeight;

            try {
                const response = await fetch(`${API_BASE}/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text, report_context: currentReportContext })
                });
                const data = await response.json();
                typingDiv.remove();
                if (data.success) {
                    addMessage(data.reply, 'ai');
                } else {
                    addMessage("Sorry, I am having trouble understanding. Error: " + data.error, 'ai');
                }
            } catch (err) {
                typingDiv.remove();
                addMessage("Sorry, I am having trouble connecting to the server. Please try again.", 'ai');
            }
        }

        function addMessage(text, sender) {
            const div = document.createElement('div');
            div.className = `msg ${sender}`;
            div.innerText = text;
            chatBody.appendChild(div);
            chatBody.scrollTop = chatBody.scrollHeight;
        }

        function downloadPDF() {
            const element = document.getElementById('report-container');
            const btn = document.getElementById('download-btn');
            btn.style.display = 'none';
            const opt = {
                margin: 10,
                filename: 'MediScan_Clinical_Report.pdf',
                image: { type: 'jpeg', quality: 0.98 },
                html2canvas: { scale: 2, useCORS: true, backgroundColor: '#ffffff' },
                jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
            };
            html2pdf().set(opt).from(element).save().then(() => { btn.style.display = 'flex'; });
        }
    