import re

with open('static/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the HTML block inside #report-container
new_report_html = '''<div class="report-header">
                    <h2>MEDISCAN AI — CLINICAL REPORT</h2>
                    <p style="font-family: var(--font-mono); color: var(--text-secondary); margin-top: 8px;">Date: <span id="current-date"></span></p>
                </div>

                <div class="patient-summary">
                    <div class="summary-pill">Name: <b id="rep-name">--</b></div>
                    <div class="summary-pill">Age: <b id="rep-age">--</b></div>
                    <div class="summary-pill">Gender: <b id="rep-gender">--</b></div>
                    <div class="summary-pill">Blood Type: <b id="rep-blood">--</b></div>
                    <div class="summary-pill">Smoking: <b id="rep-smoking">--</b></div>
                    <div class="summary-pill">Alcohol: <b id="rep-alcohol">--</b></div>
                    <div class="summary-pill">Family Hist: <b id="rep-family">--</b></div>
                </div>

                <div style="display: flex; gap: 10px; margin-bottom: 30px;">
                    <span class="badge" id="rep-image-type" style="background: rgba(255, 179, 71, 0.2); border: 1px solid var(--warning); color: var(--warning);">Image: --</span>
                    <span class="badge" id="rep-body-region" style="background: rgba(255,255,255,0.1); border:1px solid rgba(255,255,255,0.2); color:white;">Region: --</span>
                    <span class="badge" id="rep-image-quality" style="background: rgba(0, 255, 136, 0.2); border: 1px solid var(--secondary); color: var(--secondary);">Quality: --</span>
                </div>

                <!-- Cancer Risk Section -->
                <div class="risk-section">
                    <h3 style="margin-bottom: 25px; font-size: 1.5rem; letter-spacing: 1px;">CANCER RISK ASSESSMENT</h3>
                    
                    <div class="gauge-container">
                        <div class="gauge-background"></div>
                        <div class="gauge-fill" id="risk-gauge"></div>
                        <div class="gauge-cover">
                            <div class="gauge-text" id="risk-score">0</div>
                            <div class="gauge-label">Score / 100</div>
                        </div>
                    </div>
                    
                    <div class="risk-badges">
                        <div class="badge" id="risk-level-badge" style="font-size: 1.1rem; padding: 12px 24px; font-weight: 700;">--</div>
                        <div class="badge" id="risk-stage-badge" style="font-size: 1.1rem; padding: 12px 24px; font-weight: 700;">--</div>
                    </div>
                    <div style="margin-top: 20px; font-weight: 700; color: var(--text-primary); font-size: 1.25rem; background: rgba(0,0,0,0.2); padding: 15px; border-radius: 8px;">
                        Suspected Type: <span id="risk-suspected-type">--</span>
                    </div>
                    <div style="margin-top: 15px; color: var(--text-secondary); font-size: 0.95rem; padding: 0 10px;" id="risk-reasoning">
                        --
                    </div>
                </div>

                <!-- Key Findings -->
                <h3 class="section-heading">Key Findings</h3>
                <div id="findings-container">
                    <!-- Dynamic findings will go here -->
                </div>

                <!-- Possible Conditions -->
                <h3 class="section-heading" style="margin-top: 40px;">Differential Diagnosis</h3>
                <div class="conditions-grid" id="conditions-container">
                    <!-- Dynamic conditions will go here -->
                </div>

                <!-- Next Steps -->
                <h3 class="section-heading" style="margin-top: 40px;">Recommended Next Steps</h3>
                <div class="step-list" id="next-steps-container">
                    <!-- Dynamic steps will go here -->
                </div>

                <!-- Validator Section -->
                <div class="validator-card">
                    <div class="validator-header">
                        <span style="font-weight: 700; color: var(--secondary); font-size: 1.1rem;" id="validator-title">Agent 3: Validator</span>
                        <span style="font-family: var(--font-mono); font-weight: bold;" id="validator-score-text">Reliability: --/10</span>
                    </div>
                    <div class="validator-bar-bg"><div class="validator-bar-fill" id="validator-bar-fill" style="width: 0%;"></div></div>
                    <div style="display: flex; gap: 10px; margin-top: 15px; flex-wrap: wrap;" id="validator-flags-container">
                        <span class="badge badge-success" id="validator-verdict" style="font-weight: bold;">VERDICT: --</span>
                        <span class="badge" id="validator-note" style="background: rgba(255,255,255,0.05); border-color: rgba(255,255,255,0.2);">--</span>
                    </div>
                </div>

                <div style="background: rgba(255, 179, 71, 0.1); border: 1px solid var(--warning); padding: 15px; border-radius: 8px; margin-bottom: 20px; text-align: center; color: var(--text-secondary); font-size: 0.95rem;">
                    MediScan AI is an assistive AI tool. Reports are not a substitute for professional medical diagnosis. Always consult a licensed physician.
                </div>'''

# We will replace from <div class="report-header"> up to the warning block
content = re.sub(r'<div class="report-header">.*?MediScan AI is an assistive AI tool.*?</div\s*>', new_report_html, content, flags=re.DOTALL)


# Now we replace the <script> logic
new_script = '''
    <script>
        const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
            ? 'http://localhost:5000' 
            : '';
        let currentReportContext = null;

        function showToast(type, message) {
            const container = document.getElementById('toast-container');
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            
            let icon = '';
            if (type === 'success') icon = '✅';
            if (type === 'error') icon = '❌';
            if (type === 'warning') icon = '⚠️';
            
            toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
            container.appendChild(toast);
            
            setTimeout(() => {
                toast.classList.add('fade-out');
                setTimeout(() => toast.remove(), 300);
            }, 4000);
        }

        const options = { year: 'numeric', month: 'short', day: 'numeric' };
        document.getElementById('current-date').innerText = new Date().toLocaleDateString('en-US', options);

        tsParticles.load("tsparticles", {
            fpsLimit: 30,
            interactivity: { events: { onHover: { enable: false }, resize: true } },
            particles: {
                color: { value: "#00d4ff" },
                links: { color: "#00d4ff", distance: 150, enable: true, opacity: 0.1, width: 1 },
                move: { direction: "none", enable: true, outModes: { default: "out" }, random: false, speed: 0.3, straight: false },
                number: { density: { enable: true, area: 1000 }, value: 40 },
                opacity: { value: 0.3 },
                shape: { type: "circle" },
                size: { value: { min: 1, max: 2 } }
            },
            detectRetina: false
        });

        function showPage(pageId) {
            document.querySelectorAll('.page').forEach(p => p.classList.add('hidden'));
            document.getElementById('page-' + pageId).classList.remove('hidden');
            window.scrollTo(0, 0);
        }

        let currentStep = 1;
        const resultsPlaceholder = document.getElementById('results-placeholder');
        const reportContainer = document.getElementById('report-container');

        let currentMainScanFile = null;
        let currentPdfFile = null;
        let currentExtraFile = null;

        function goToStep(step) {
            if(step === 4) {
                const nameInput = document.getElementById('pat-name');
                const ageInput = document.getElementById('pat-age');
                let valid = true;
                if(!nameInput.value) { nameInput.style.borderColor = 'var(--danger)'; valid = false; }
                else { nameInput.style.borderColor = ''; }
                if(!ageInput.value) { ageInput.style.borderColor = 'var(--danger)'; valid = false; }
                else { ageInput.style.borderColor = ''; }
                if(!valid) return;
            }

            document.querySelectorAll('.wizard-step-content').forEach(el => el.classList.remove('active'));
            document.getElementById('step-' + step + '-content').classList.add('active');

            for(let i=1; i<=4; i++) {
                const nav = document.getElementById('nav-step-' + i);
                const circle = document.getElementById('nav-circle-' + i);
                if(i < step) { nav.classList.add('completed'); nav.classList.remove('active'); circle.innerHTML = "✓"; }
                else if(i === step) { nav.classList.add('active'); nav.classList.remove('completed'); circle.innerHTML = i; }
                else { nav.classList.remove('active', 'completed'); circle.innerHTML = i; }
                if(i < 4) {
                    const lineFill = document.getElementById('line-fill-' + i);
                    if(i < step) lineFill.style.width = '100%'; else lineFill.style.width = '0%';
                }
            }
            currentStep = step;
            if(step === 4) startAnalysis();
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
                document.getElementById('main-scan-info').innerText = `${file.name} (${(file.size/1024/1024).toFixed(2)} MB)`;
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
            nextBtn.disabled = true; nextBtn.style.opacity = '0.5'; nextBtn.style.cursor = 'not-allowed';
        }

        const pdfInput = document.getElementById('pdf-input');
        const pdfZone = document.getElementById('pdf-zone');
        pdfZone.addEventListener('dragover', (e) => { e.preventDefault(); pdfZone.classList.add('dragover'); });
        pdfZone.addEventListener('dragleave', () => { pdfZone.classList.remove('dragover'); });
        pdfZone.addEventListener('drop', (e) => { e.preventDefault(); pdfZone.classList.remove('dragover'); if(e.dataTransfer.files[0]) handlePdf(e.dataTransfer.files[0]); });
        pdfInput.addEventListener('change', (e) => { if(e.target.files[0]) handlePdf(e.target.files[0]); });

        function handlePdf(file) {
            if(file.type !== 'application/pdf') return alert('Please upload a PDF file.');
            currentPdfFile = file;
            document.getElementById('pdf-info').innerText = file.name;
            document.getElementById('pdf-idle').style.display = 'none';
            document.getElementById('pdf-preview').style.display = 'block';
            pdfZone.classList.add('uploaded');
        }
        function removePdf() {
            pdfInput.value = "";
            currentPdfFile = null;
            document.getElementById('pdf-idle').style.display = 'block';
            document.getElementById('pdf-preview').style.display = 'none';
            pdfZone.classList.remove('uploaded');
        }

        const extraInput = document.getElementById('extra-input');
        const extraZone = document.getElementById('extra-zone');
        extraZone.addEventListener('dragover', (e) => { e.preventDefault(); extraZone.classList.add('dragover'); });
        extraZone.addEventListener('dragleave', () => { extraZone.classList.remove('dragover'); });
        extraZone.addEventListener('drop', (e) => { e.preventDefault(); extraZone.classList.remove('dragover'); if(e.dataTransfer.files[0]) handleExtra(e.dataTransfer.files[0]); });
        extraInput.addEventListener('change', (e) => { if(e.target.files[0]) handleExtra(e.target.files[0]); });

        function handleExtra(file) {
            if(!file.type.startsWith('image/')) return alert('Please upload an image.');
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
            extraInput.value = "";
            currentExtraFile = null;
            document.getElementById('extra-idle').style.display = 'block';
            document.getElementById('extra-preview').style.display = 'none';
            extraZone.classList.remove('uploaded');
        }

        function setStepActive(id, text) {
            document.getElementById(id).classList.add('active');
            document.getElementById(id + '-text').innerHTML = `<span class='loading-spinner' style='width:12px;height:12px;border-width:2px;margin-right:5px;'></span>${text}`;
        }

        function setStepDone(id, text) {
            const step = document.getElementById(id);
            step.classList.remove('active');
            step.classList.add('done');
            step.querySelector('.step-indicator').innerHTML = "✓";
            document.getElementById(id + '-text').innerText = text;
        }

        async function startAnalysis() {
            if (!currentMainScanFile) {
                showToast('error', 'Please upload a medical scan first');
                goToStep(1); // revert back
                return;
            }

            const nameVal = document.getElementById('pat-name').value;
            const ageVal = document.getElementById('pat-age').value;
            const genderBtn = document.querySelector('#pat-gender .segment-btn.active');
            const genderVal = genderBtn ? genderBtn.innerText : "";
            
            const bloodVal = document.getElementById('pat-blood').value;
            const scanTypeBtn = document.querySelector('#pat-scan-type .card-btn.active');
            const scanTypeVal = scanTypeBtn ? scanTypeBtn.innerText : "";
            const regionBtn = document.querySelector('#pat-region .card-btn.active');
            const regionVal = regionBtn ? regionBtn.innerText : "";
            
            const conditionsVal = document.getElementById('pat-conditions').value;
            const symptomsVal = document.getElementById('pat-symptoms').value;
            
            const toggles = document.querySelectorAll('.toggle-switch');
            const smokingVal = toggles[0].classList.contains('active') ? 'Yes' : 'No';
            const alcoholVal = toggles[1].classList.contains('active') ? 'Yes' : 'No';
            const familyVal = toggles[2].classList.contains('active') ? 'Yes' : 'No';

            // Loading state
            const runBtn = document.getElementById('run-analysis-btn');
            runBtn.disabled = true;
            runBtn.innerHTML = 'Analyzing... ⏳';
            runBtn.style.opacity = '0.7';
            
            // Disable inputs
            document.querySelectorAll('input, select, textarea, .segment-btn, .card-btn, .toggle-switch').forEach(el => {
                if(el.tagName === 'DIV' || el.tagName === 'BUTTON') el.style.pointerEvents = 'none';
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

            setStepActive('step-1-agent', "🔬 Analyzing image with Vision AI...");

            // Prepare FormData
            const formData = new FormData();
            formData.append('scan_image', currentMainScanFile);
            
            if (currentPdfFile) formData.append('report_pdf', currentPdfFile);
            
            if (currentExtraFile) formData.append('additional_image', currentExtraFile);

            if(nameVal) formData.append('patient_name', nameVal);
            if(ageVal) formData.append('age', ageVal);
            if(genderVal) formData.append('gender', genderVal);
            if(bloodVal !== 'Unknown') formData.append('blood_type', bloodVal);
            if(scanTypeVal) formData.append('scan_type', scanTypeVal);
            if(regionVal) formData.append('body_region', regionVal);
            if(conditionsVal) formData.append('known_conditions', conditionsVal);
            if(symptomsVal) formData.append('symptoms', symptomsVal);
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
                    setStepDone('step-1-agent', "Pattern extraction complete");
                    setStepActive('step-2-agent', "🧠 Generating clinical report...");
                    
                    setTimeout(() => { 
                        setStepDone('step-2-agent', "Report generated"); 
                        setStepActive('step-3-agent', "✅ Validating report..."); 
                        
                        setTimeout(() => { 
                            setStepDone('step-3-agent', "Validation complete");
                            document.getElementById('analysis-done-msg').classList.remove('hidden');
                            
                            const nav4 = document.getElementById('nav-step-4');
                            nav4.classList.add('completed');
                            nav4.classList.remove('active');
                            document.getElementById('nav-circle-4').innerHTML = "✓";

                            populateReport(data);
                            currentReportContext = JSON.stringify(data.report);
                            showToast('success', 'Analysis complete!');
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
                // Re-enable inputs
                runBtn.disabled = false;
                runBtn.innerHTML = 'Run Analysis 🔬';
                runBtn.style.opacity = '1';
                document.querySelectorAll('input, select, textarea, .segment-btn, .card-btn, .toggle-switch').forEach(el => {
                    if(el.tagName === 'DIV' || el.tagName === 'BUTTON') el.style.pointerEvents = 'all';
                    else el.disabled = false;
                });
            }
        }

        function populateReport(data) {
            const r = data.report || {};
            const v = data.validation || {};
            const p = data.patient || {};

            // Summary
            document.getElementById('rep-name').innerText = p.patient_name || '--';
            document.getElementById('rep-age').innerText = p.age || '--';
            document.getElementById('rep-gender').innerText = p.gender || '--';
            document.getElementById('rep-blood').innerText = p.blood_type || '--';
            document.getElementById('rep-smoking').innerText = p.smoking || '--';
            document.getElementById('rep-alcohol').innerText = p.alcohol || '--';
            document.getElementById('rep-family').innerText = p.family_history || '--';

            // Badges
            document.getElementById('rep-image-type').innerText = `Image: ${r.image_type || '--'}`;
            document.getElementById('rep-body-region').innerText = `Region: ${r.body_region || '--'}`;
            document.getElementById('rep-image-quality').innerText = `Quality: ${r.image_quality?.overall || '--'}`;

            // Risk Assessment
            const riskObj = r.cancer_risk || {};
            const riskScoreTarget = riskObj.risk_score || 0;
            document.getElementById('risk-level-badge').innerText = riskObj.risk_level ? riskObj.risk_level.toUpperCase() : '--';
            document.getElementById('risk-stage-badge').innerText = riskObj.stage ? `STAGE: ${riskObj.stage.toUpperCase()}` : '--';
            document.getElementById('risk-suspected-type').innerText = riskObj.suspected_type || '--';
            document.getElementById('risk-reasoning').innerText = riskObj.reasoning || '--';

            // Risk Colors
            const lvl = (riskObj.risk_level || '').toLowerCase();
            const badgeLvl = document.getElementById('risk-level-badge');
            if (lvl.includes('high') || lvl.includes('critical')) { badgeLvl.className = 'badge badge-danger'; }
            else if (lvl.includes('moderate')) { badgeLvl.className = 'badge badge-warning'; }
            else { badgeLvl.className = 'badge badge-success'; }

            // Findings
            const findingsHtml = (r.findings || []).map((f, i) => `
                <div class="finding-card">
                    <b>${i+1}. ${f.category || 'Observation'}:</b> ${f.description || ''} 
                    <span style="opacity: 0.7; font-size: 0.85rem; margin-left: 10px;">(${f.severity || 'Unknown'})</span>
                </div>
            `).join('');
            document.getElementById('findings-container').innerHTML = findingsHtml || '<p style="color:var(--text-secondary)">No specific findings reported.</p>';

            // Conditions
            const conditionsHtml = (r.conditions || []).map(c => {
                let colorClass = 'var(--secondary)';
                let confWidth = '30%';
                if (c.confidence === 'high') { colorClass = 'var(--danger)'; confWidth = '85%'; }
                else if (c.confidence === 'medium') { colorClass = 'var(--warning)'; confWidth = '60%'; }

                return `
                <div class="condition-card">
                    <div style="font-weight: 700; font-size: 1.1rem;">${c.name || 'Unknown Condition'}</div>
                    <div class="confidence-bar"><div class="confidence-fill" style="width: ${confWidth}; background: ${colorClass};"></div></div>
                    <div style="font-size: 0.85rem; color: var(--text-secondary);"><b>${c.confidence ? c.confidence.toUpperCase() : ''} Confidence.</b> ${c.reasoning || ''}</div>
                </div>
                `;
            }).join('');
            document.getElementById('conditions-container').innerHTML = conditionsHtml || '<p style="color:var(--text-secondary)">No specific differential diagnosis.</p>';

            // Next Steps
            const stepsHtml = (r.next_steps || []).map((ns, i) => {
                let badgeClass = 'badge-success';
                let urg = (ns.urgency || '').toLowerCase();
                if (urg === 'urgent' || urg === 'immediate') badgeClass = 'badge-danger';
                else if (urg === 'soon') badgeClass = 'badge-warning';

                return `
                <div class="action-card">
                    <div class="action-number">${i+1}</div>
                    <div style="flex: 1;">
                        <div style="font-weight: 700; font-size: 1.1rem; margin-bottom: 4px;">${ns.action || ''}</div>
                        <div style="font-size: 0.95rem; color: var(--text-secondary);">${ns.reason || ''}</div>
                    </div>
                    <div class="badge ${badgeClass}" style="font-weight: bold;">${ns.urgency || 'Routine'}</div>
                </div>
                `;
            }).join('');
            document.getElementById('next-steps-container').innerHTML = stepsHtml || '<p style="color:var(--text-secondary)">No immediate next steps recommended.</p>';

            // Validator
            document.getElementById('validator-score-text').innerText = `Reliability: ${v.reliability_score || 0}/10`;
            document.getElementById('validator-bar-fill').style.width = `${(v.reliability_score || 0) * 10}%`;
            document.getElementById('validator-verdict').innerText = `VERDICT: ${v.verdict || '--'}`;
            
            const vVerdict = (v.verdict || '').toLowerCase();
            const vBadge = document.getElementById('validator-verdict');
            if (vVerdict.includes('pass') && !vVerdict.includes('warning')) { vBadge.className = 'badge badge-success'; }
            else if (vVerdict.includes('fail')) { vBadge.className = 'badge badge-danger'; }
            else { vBadge.className = 'badge badge-warning'; }

            document.getElementById('validator-note').innerText = v.validator_note || '--';

            // Flags
            let flagsHtml = `<span class="badge ${vBadge.className}" id="validator-verdict" style="font-weight: bold;">VERDICT: ${v.verdict || '--'}</span>`;
            flagsHtml += `<span class="badge" id="validator-note" style="background: rgba(255,255,255,0.05); border-color: rgba(255,255,255,0.2);">${v.validator_note || '--'}</span>`;
            (v.flags || []).forEach(f => {
                flagsHtml += `<span class="badge badge-warning" style="background: rgba(255, 179, 71, 0.1); border: 1px solid var(--warning);">${f}</span>`;
            });
            document.getElementById('validator-flags-container').innerHTML = flagsHtml;

            showReport(riskScoreTarget);
        }

        function showReport(targetScore) {
            resultsPlaceholder.classList.add('hidden');
            reportContainer.classList.remove('hidden');
            
            setTimeout(() => {
                const gaugeFill = document.getElementById('risk-gauge');
                const scoreText = document.getElementById('risk-score');
                
                let currentPercent = 0;
                
                const animate = () => {
                    if(currentPercent <= targetScore) {
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
                reportContainer.scrollIntoView({behavior: 'smooth', block: 'start'});
            }, 100);
        }

        function resetWizard() {
            goToStep(1);
        }

        // Chatbot Logic
        const chatWindow = document.getElementById('chat-window');
        const chatBody = document.getElementById('chat-body');
        const chatInput = document.getElementById('chat-input');

        function toggleChat() {
            chatWindow.classList.toggle('open');
            if(chatWindow.classList.contains('open')) {
                setTimeout(() => chatInput.focus(), 300);
            }
        }

        function handleChatKey(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        }

        async function sendMessage() {
            const text = chatInput.value.trim();
            if(!text) return;

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
                    body: JSON.stringify({
                        message: text,
                        report_context: currentReportContext
                    })
                });
                
                const data = await response.json();
                typingDiv.remove();
                
                if (data.success) {
                    addMessage(data.reply, 'ai');
                } else {
                    addMessage("Sorry, I'm having trouble understanding. Error: " + data.error, 'ai');
                }
            } catch (err) {
                typingDiv.remove();
                addMessage("Sorry, I'm having trouble connecting to the server. Please try again.", 'ai');
            }
        }

        function addMessage(text, sender) {
            const div = document.createElement('div');
            div.className = `msg ${sender}`;
            div.innerText = text;
            chatBody.appendChild(div);
            chatBody.scrollTop = chatBody.scrollHeight;
        }
    </script>
'''

content = re.sub(r'<script>.*?</script>', new_script, content, flags=re.DOTALL)

with open('static/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
