// Protégé Web Application Frontend
document.addEventListener('DOMContentLoaded', () => {
  // State
  let sessionId = null;
  let currentDoc = null;
  let selectedQuestions = 5;
  let selectedPersona = 'novice';
  let totalQuestions = 5;
  let currentQuestionNum = 1;
  let isSending = false;

  // DOM Elements
  const llmModeText = document.getElementById('llmModeText');
  const resetSessionBtn = document.getElementById('resetSessionBtn');

  // New Landing & Hint Elements
  const landingScreen = document.getElementById('landingScreen');
  const hintScreen = document.getElementById('hintScreen');
  const btnHintMode = document.getElementById('btnHintMode');
  const btnTeacherMode = document.getElementById('btnTeacherMode');
  const hintConceptInput = document.getElementById('hintConceptInput');
  const startHintSessionBtn = document.getElementById('startHintSessionBtn');
  const hintInteractionArea = document.getElementById('hintInteractionArea');
  const hintDisplay = document.getElementById('hintDisplay');
  const hintUserInput = document.getElementById('hintUserInput');
  const getHintBtn = document.getElementById('getHintBtn');
  const btnBackFromHint = document.getElementById('btnBackFromHint');
  const btnBackFromTeacher = document.getElementById('btnBackFromTeacher');
  const themeToggleBtn = document.getElementById('themeToggleBtn');
  const themeIconLight = document.getElementById('themeIconLight');
  const themeIconDark = document.getElementById('themeIconDark');

    // --- Dashboard Metrics Initialization ---
  async function initDashboard() {
    const modesPieChartCtx = document.getElementById('modesPieChart');
    const scoresBarChartCtx = document.getElementById('scoresBarChart');
    if (!modesPieChartCtx || !scoresBarChartCtx) return;

    try {
      const res = await fetch('/api/metrics');
      const data = await res.json();

      // Update counters
      document.getElementById('streakDays').textContent = data.streak_days;
      document.getElementById('totalSessions').textContent = data.total_sessions;

      // Theme colors based on body text
      const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
      const textColor = isDark ? '#FFFFFF' : '#000000';
      const gridColor = isDark ? '#333333' : '#E5E5E5';

      // Pie Chart
      new Chart(modesPieChartCtx, {
        type: 'doughnut',
        data: {
          labels: Object.keys(data.modes_distribution),
          datasets: [{
            data: Object.values(data.modes_distribution),
            backgroundColor: [isDark ? '#FFFFFF' : '#000000', isDark ? '#666666' : '#999999'],
            borderWidth: 0
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'right',
              labels: { color: textColor, font: { family: 'Plus Jakarta Sans' } }
            }
          }
        }
      });

      // Bar Chart
      new Chart(scoresBarChartCtx, {
        type: 'bar',
        data: {
          labels: data.mastery_scores.labels,
          datasets: [
            {
              label: 'Accuracy',
              data: data.mastery_scores.accuracy,
              backgroundColor: isDark ? '#FFFFFF' : '#000000',
              borderRadius: 4
            },
            {
              label: 'Clarity',
              data: data.mastery_scores.clarity,
              backgroundColor: isDark ? '#666666' : '#999999',
              borderRadius: 4
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { labels: { color: textColor, font: { family: 'Plus Jakarta Sans' } } }
          },
          scales: {
            y: {
              beginAtZero: true,
              max: 100,
              grid: { color: gridColor },
              ticks: { color: textColor }
            },
            x: {
              grid: { display: false },
              ticks: { color: textColor }
            }
          }
        }
      });
    } catch (e) {
      console.error('Failed to load dashboard metrics', e);
    }
  }

  // Initialize dashboard when the page loads
  initDashboard();

  // --- End Dashboard Metrics ---


  const btnMaterialsMode = document.getElementById('btnMaterialsMode');
  const materialsScreen = document.getElementById('materialsScreen');
  const btnBackFromMaterials = document.getElementById('btnBackFromMaterials');
  const materialsDropZone = document.getElementById('materialsDropZone');
  const materialsFileInput = document.getElementById('materialsFileInput');
  const materialsUploadStatus = document.getElementById('materialsUploadStatus');
  const materialsList = document.getElementById('materialsList');
  
  const tabLibraryMode = document.getElementById('tabLibraryMode');
  const paneLibraryMode = document.getElementById('paneLibraryMode');
  const teacherMaterialSelect = document.getElementById('teacherMaterialSelect');
  const useLibraryBtn = document.getElementById('useLibraryBtn');
  const hintMaterialSelect = document.getElementById('hintMaterialSelect');

  async function loadMaterials() {
    try {
      const res = await fetch('/api/materials');
      if (res.ok) {
        const materials = await res.json();
        
        if(materialsList) {
            materialsList.innerHTML = materials.length ? '' : '<em>No materials uploaded yet.</em>';
            materials.forEach(m => {
              const div = document.createElement('div');
              div.style = 'padding: 10px; background: var(--bg-surface); border: 1px solid var(--border-color); border-radius: 6px;';
              div.innerHTML = `<strong>${m.title}</strong> (${m.words} words) - ${m.type}`;
              materialsList.appendChild(div);
            });
        }

        let optionsHtml = '<option value="">-- No Material Selected --</option>';
        materials.forEach(m => {
          optionsHtml += `<option value="${m.id}">${m.title}</option>`;
        });
        if(teacherMaterialSelect) teacherMaterialSelect.innerHTML = optionsHtml;
        if(hintMaterialSelect) hintMaterialSelect.innerHTML = optionsHtml;
      }
    } catch (e) {
      console.error('Failed to load materials', e);
    }
  }
  
  loadMaterials();

  if (btnMaterialsMode) {
    btnMaterialsMode.addEventListener('click', () => {
      landingScreen.style.display = 'none';
      materialsScreen.style.display = 'block';
      loadMaterials();
    });
  }

  if (btnBackFromMaterials) {
    btnBackFromMaterials.addEventListener('click', () => {
      materialsScreen.style.display = 'none';
      landingScreen.style.display = 'block';
    });
  }

  if (materialsDropZone) {
    materialsDropZone.addEventListener('dragover', (e) => { e.preventDefault(); materialsDropZone.classList.add('dragover'); });
    materialsDropZone.addEventListener('dragleave', () => { materialsDropZone.classList.remove('dragover'); });
    materialsDropZone.addEventListener('drop', (e) => {
      e.preventDefault(); materialsDropZone.classList.remove('dragover');
      if (e.dataTransfer.files.length > 0) uploadMaterial(e.dataTransfer.files[0]);
    });
    materialsFileInput.addEventListener('change', (e) => {
      if (e.target.files.length > 0) uploadMaterial(e.target.files[0]);
    });
  }

  async function uploadMaterial(file) {
    materialsUploadStatus.textContent = 'Uploading...';
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await fetch('/api/materials/upload', {
        method: 'POST',
        body: formData
      });
      if (res.ok) {
        materialsUploadStatus.textContent = 'Uploaded successfully!';
        loadMaterials();
      } else {
        const data = await res.json();
        materialsUploadStatus.textContent = 'Upload failed: ' + (data.error || 'Unknown error');
      }
    } catch (e) {
      materialsUploadStatus.textContent = 'Upload failed: Network error';
    }
  }

  if (tabLibraryMode) {
    tabLibraryMode.addEventListener('click', () => {
      tabLibraryMode.classList.add('active');
      document.getElementById('tabDocMode').classList.remove('active');
      document.getElementById('tabTopicMode').classList.remove('active');
      paneLibraryMode.style.display = 'block';
      document.getElementById('paneDocMode').style.display = 'none';
      document.getElementById('paneTopicMode').style.display = 'none';
    });
    document.getElementById('tabDocMode').addEventListener('click', () => {
      if(tabLibraryMode) tabLibraryMode.classList.remove('active');
      if(paneLibraryMode) paneLibraryMode.style.display = 'none';
    });
    document.getElementById('tabTopicMode').addEventListener('click', () => {
      if(tabLibraryMode) tabLibraryMode.classList.remove('active');
      if(paneLibraryMode) paneLibraryMode.style.display = 'none';
    });
  }
  
  if (useLibraryBtn) {
    useLibraryBtn.addEventListener('click', async () => {
      const matId = teacherMaterialSelect.value;
      if (!matId) return alert('Please select a material.');
      setLoadingState(true, 'Loading from library...');
      try {
        const res = await fetch('/api/upload', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ material_id: matId }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Failed to load library material');
        onDocumentLoaded(data);
      } catch (err) {
        alert('Error: ' + err.message);
      } finally {
        setLoadingState(false);
      }
    });
  }


  // Theme Logic (Default to light)
  let isDarkMode = false;
  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
      isDarkMode = !isDarkMode;
      if (isDarkMode) {
        document.documentElement.setAttribute('data-theme', 'dark');
        themeIconLight.style.display = 'none';
        themeIconDark.style.display = 'block';
      } else {
        document.documentElement.removeAttribute('data-theme');
        themeIconLight.style.display = 'block';
        themeIconDark.style.display = 'none';
      }
    });
  }

  if (btnTeacherMode) {
    btnTeacherMode.addEventListener('click', () => {
      landingScreen.style.display = 'none';
      setupScreen.style.display = 'block';
    });
  }

  if (btnHintMode) {
    btnHintMode.addEventListener('click', () => {
      landingScreen.style.display = 'none';
      hintScreen.style.display = 'block';
    });
  }

  if (btnBackFromHint) {
    btnBackFromHint.addEventListener('click', () => {
      hintScreen.style.display = 'none';
      landingScreen.style.display = 'block';
    });
  }

  if (btnBackFromTeacher) {
    btnBackFromTeacher.addEventListener('click', () => {
      setupScreen.style.display = 'none';
      landingScreen.style.display = 'block';
    });
  }

  const btnPomodoroMode = document.getElementById('btnPomodoroMode');
  const pomodoroScreen = document.getElementById('pomodoroScreen');
  const btnBackFromPomodoro = document.getElementById('btnBackFromPomodoro');

  if (btnPomodoroMode) {
    btnPomodoroMode.addEventListener('click', () => {
      landingScreen.style.display = 'none';
      pomodoroScreen.style.display = 'block';
    });
  }

  if (btnBackFromPomodoro) {
    btnBackFromPomodoro.addEventListener('click', () => {
      pomodoroScreen.style.display = 'none';
      landingScreen.style.display = 'block';
    });
  }

  const btnTodoListMode = document.getElementById('btnTodoListMode');
  const todoListScreen = document.getElementById('todoListScreen');
  const btnBackFromTodo = document.getElementById('btnBackFromTodo');

  if (btnTodoListMode) {
    btnTodoListMode.addEventListener('click', () => {
      landingScreen.style.display = 'none';
      todoListScreen.style.display = 'block';
    });
  }

  if (btnBackFromTodo) {
    btnBackFromTodo.addEventListener('click', () => {
      todoListScreen.style.display = 'none';
      landingScreen.style.display = 'block';
    });
  }

  let hintSessionId = null;

  if (startHintSessionBtn) {
    startHintSessionBtn.addEventListener('click', async () => {
      const concept = hintConceptInput.value.trim();
      if (!concept) return alert('Please enter a concept.');
      hintSessionId = 'hint_' + Math.random().toString(36).substr(2, 9);
      hintInteractionArea.style.display = 'block';
      hintDisplay.innerHTML = `<em>Requesting first hint for "${concept}"...</em>`;
      startHintSessionBtn.disabled = true;
      hintConceptInput.disabled = true;
      
      await fetchHint(concept);
    });
  }

  if (getHintBtn) {
    getHintBtn.addEventListener('click', async () => {
      const concept = hintConceptInput.value.trim();
      const userAnswer = hintUserInput.value.trim();
      hintDisplay.innerHTML += `<br/><br/><strong>You:</strong> ${userAnswer || "(Requested next hint)"}`;
      hintUserInput.value = '';
      await fetchHint(concept, userAnswer);
    });
  }

  async function fetchHint(conceptId, userAns = "") {
    try {
      const res = await fetch('/api/hint', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: hintSessionId, concept_id: conceptId, user_last_answer: userAns, material_id: document.getElementById("hintMaterialSelect") ? document.getElementById("hintMaterialSelect").value : "" })
      });
      const data = await res.json();
      if (res.ok) {
        if (data.level === 99) {
          hintDisplay.innerHTML += `<br/><br/><strong style="color:green;">Correct!</strong> ${data.hint}`;
          if (getHintBtn) getHintBtn.disabled = true;
          if (hintUserInput) hintUserInput.disabled = true;
        } else {
          hintDisplay.innerHTML += `<br/><br/><strong>Hint (Level ${data.level}):</strong> ${data.hint}`;
        }
      } else {
        const errorMsg = data.hint || data.error;
        alert(errorMsg);
        hintDisplay.innerHTML += `<br/><br/><span style="color:red;">Error: ${errorMsg}</span>`;
      }
    } catch (e) {
      alert("Network Error");
      hintDisplay.innerHTML += `<br/><br/><span style="color:red;">Network Error</span>`;
    }
  }

  // Setup Screen
  const setupScreen = document.getElementById('setupScreen');
  const tabDocMode = document.getElementById('tabDocMode');
  const tabTopicMode = document.getElementById('tabTopicMode');
  const paneDocMode = document.getElementById('paneDocMode');
  const paneTopicMode = document.getElementById('paneTopicMode');
  const topicInput = document.getElementById('topicInput');
  const researchTopicBtn = document.getElementById('researchTopicBtn');
  const dropZone = document.getElementById('dropZone');
  const fileInput = document.getElementById('fileInput');
  const useSampleBtn = document.getElementById('useSampleBtn');
  const fileSummaryCard = document.getElementById('fileSummaryCard');
  const summaryFileName = document.getElementById('summaryFileName');
  const summaryWordCount = document.getElementById('summaryWordCount');
  const topicsTags = document.getElementById('topicsTags');
  const changeFileBtn = document.getElementById('changeFileBtn');
  const configSection = document.getElementById('configSection');
  const questionCountPills = document.getElementById('questionCountPills');
  const customCountBtn = document.getElementById('customCountBtn');
  const customCountInput = document.getElementById('customCountInput');
  const personaCards = document.querySelectorAll('.persona-card');
  const startSessionBtn = document.getElementById('startSessionBtn');

  // Classroom Chat Screen
  const chatScreen = document.getElementById('chatScreen');
  const sidebarStudentAvatar = document.getElementById('sidebarStudentAvatar');
  const sidebarStudentName = document.getElementById('sidebarStudentName');
  const studentStateBadge = document.getElementById('studentStateBadge');
  const progressCounter = document.getElementById('progressCounter');
  const progressBarFill = document.getElementById('progressBarFill');
  const curriculumList = document.getElementById('curriculumList');
  const currentTopicTitle = document.getElementById('currentTopicTitle');
  const chatMessages = document.getElementById('chatMessages');
  const chatForm = document.getElementById('chatForm');
  const userInput = document.getElementById('userInput');
  const sendBtn = document.getElementById('sendBtn');
  const btnViewReport = document.getElementById('btnViewReport');
  const btnConcludeEarly = document.getElementById('btnConcludeEarly');
  const btnRetestQuick = document.getElementById('btnRetestQuick');

  // Report Modal
  const reportModal = document.getElementById('reportModal');
  const modalReportContent = document.getElementById('modalReportContent');
  const closeReportModal = document.getElementById('closeReportModal');
  const modalRetestBtn = document.getElementById('modalRetestBtn');
  const modalCopyBtn = document.getElementById('modalCopyBtn');
  const modalNewDocBtn = document.getElementById('modalNewDocBtn');

  // 1. Initial Status Check
  async function checkServerStatus() {
    try {
      const res = await fetch('/api/status');
      if (res.ok) {
        const data = await res.json();
        llmModeText.textContent = data.active_llm_mode || 'Online';
      } else {
        llmModeText.textContent = 'Active (Local)';
      }
    } catch (e) {
      llmModeText.textContent = 'Active (Local)';
    }
  }
  checkServerStatus();

  // Tab Switching
  document.getElementById('tabDocMode').addEventListener('click', () => {
    tabDocMode.classList.add('active');
    document.getElementById('tabTopicMode').classList.remove('active');
    paneDocMode.style.display = 'block';
    document.getElementById('paneTopicMode').style.display = 'none';
  });

  document.getElementById('tabTopicMode').addEventListener('click', () => {
    tabTopicMode.classList.add('active');
    document.getElementById('tabDocMode').classList.remove('active');
    paneTopicMode.style.display = 'block';
    document.getElementById('paneDocMode').style.display = 'none';
    topicInput.focus();
  });

  // Topic Research Button & Suggestions
  researchTopicBtn.addEventListener('click', () => {
    const topic = topicInput.value.trim();
    if (topic) {
      handleTopicResearch(topic);
    }
  });

  topicInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const topic = topicInput.value.trim();
      if (topic) {
        handleTopicResearch(topic);
      }
    }
  });

  document.querySelectorAll('.topic-chip-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const topic = btn.dataset.topic;
      topicInput.value = topic;
      handleTopicResearch(topic);
    });
  });

  async function handleTopicResearch(topic) {
    setLoadingState(true, `Alex is researching '${topic}'...`);
    try {
      const res = await fetch('/api/research_topic', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic: topic }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to research topic');
      onDocumentLoaded(data);
    } catch (err) {
      alert('Error researching topic: ' + err.message);
    } finally {
      setLoadingState(false);
    }
  }

  // 2. Drag & Drop File Upload
  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
  });

  dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
  });

  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      handleFileUpload(e.target.files[0]);
    }
  });

  useSampleBtn.addEventListener('click', async () => {
    setLoadingState(true, 'Loading sample notes (Transformers)...');
    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ use_sample: true }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to load sample');
      onDocumentLoaded(data);
    } catch (err) {
      alert('Error loading sample: ' + err.message);
    } finally {
      setLoadingState(false);
    }
  });

  changeFileBtn.addEventListener('click', () => {
    fileSummaryCard.style.display = 'none';
    document.querySelector('.mode-tabs').style.display = 'flex';
    if (tabDocMode.classList.contains('active')) {
      paneDocMode.style.display = 'block';
      dropZone.style.display = 'flex';
    } else {
      paneTopicMode.style.display = 'block';
    }
    configSection.style.opacity = '0.5';
    configSection.style.pointerEvents = 'none';
    startSessionBtn.disabled = true;
    fileInput.value = '';
    topicInput.value = '';
  });

  function handleFileUpload(file) {
    setLoadingState(true, `Reading ${file.name}...`);
    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const res = await fetch('/api/upload', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            file_name: file.name,
            file_data_base64: e.target.result,
          }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Upload failed');
        onDocumentLoaded(data);
      } catch (err) {
        alert('Failed to process document: ' + err.message);
      } finally {
        setLoadingState(false);
      }
    };
    reader.onerror = () => {
      setLoadingState(false);
      alert('Failed to read file from disk.');
    };
    reader.readAsDataURL(file);
  }

  function onDocumentLoaded(data) {
    sessionId = data.session_id;
    currentDoc = data;

    summaryFileName.textContent = data.file_name;
    summaryWordCount.textContent = `${data.word_count} words`;

    topicsTags.innerHTML = '';
    (data.concepts || []).slice(0, 8).forEach(c => {
      const tag = document.createElement('span');
      tag.className = 'topic-tag';
      tag.textContent = c;
      topicsTags.appendChild(tag);
    });

    document.getElementById('paneDocMode').style.display = 'none';
    document.getElementById('paneTopicMode').style.display = 'none';
    document.querySelector('.mode-tabs').style.display = 'none';
    fileSummaryCard.style.display = 'flex';
    configSection.style.opacity = '1';
    configSection.style.pointerEvents = 'auto';
    startSessionBtn.disabled = false;
  }

  function setLoadingState(loading, text = '') {
    if (loading) {
      startSessionBtn.disabled = true;
      startSessionBtn.textContent = text || 'Loading...';
    } else {
      startSessionBtn.disabled = false;
      startSessionBtn.textContent = 'Begin Teaching Session 🚀';
    }
  }

  // 3. Question Count Selection
  questionCountPills.querySelectorAll('.pill-btn:not(.custom-pill)').forEach(btn => {
    btn.addEventListener('click', () => {
      questionCountPills.querySelectorAll('.pill-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      selectedQuestions = parseInt(btn.dataset.count, 10);
      customCountInput.style.display = 'none';
    });
  });

  customCountBtn.addEventListener('click', () => {
    questionCountPills.querySelectorAll('.pill-btn').forEach(b => b.classList.remove('active'));
    customCountBtn.classList.add('active');
    customCountInput.style.display = 'inline-block';
    customCountInput.focus();
  });

  customCountInput.addEventListener('input', (e) => {
    const val = parseInt(e.target.value, 10);
    if (!isNaN(val) && val > 0) {
      selectedQuestions = val;
    }
  });

  // 4. Persona Selection
  personaCards.forEach(card => {
    card.addEventListener('click', () => {
      personaCards.forEach(c => c.classList.remove('active'));
      card.classList.add('active');
      selectedPersona = card.dataset.persona;
    });
  });

  // 5. Start Classroom Session
  startSessionBtn.addEventListener('click', async () => {
    if (!sessionId) return;

    setLoadingState(true, 'Initializing Student Alex...');
    try {
      const res = await fetch('/api/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          num_questions: selectedQuestions,
          persona: selectedPersona,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to start');

      launchChatInterface(data);
    } catch (err) {
      alert('Error starting session: ' + err.message);
    } finally {
      setLoadingState(false);
    }
  });

  function launchChatInterface(data) {
    totalQuestions = data.total_questions;
    currentQuestionNum = 1;

    setupScreen.classList.add('collapsed');
    if (window.innerWidth <= 992) {
      setupScreen.style.display = 'flex';
    } else {
      setupScreen.style.display = 'none';
    }
    chatScreen.style.display = 'flex';
    setTimeout(() => { if (window.innerWidth <= 992) chatScreen.scrollIntoView({ behavior: 'smooth' }); }, 100);
    resetSessionBtn.style.display = 'inline-flex';

    sidebarStudentName.textContent = data.student_name;
    const personaIcons = { novice: '🧑‍🎓', peer: '🔬', pragmatic: '🛠️' };
    sidebarStudentAvatar.textContent = personaIcons[selectedPersona] || '🧑‍🎓';

    updateProgress(1, totalQuestions);
    renderCurriculum(data.concepts || [], 0);

    currentTopicTitle.textContent = data.current_concept || 'Topic 1';

    // Clear chat and append initial opening
    chatMessages.innerHTML = '';
    appendStudentMessage(data.student_opening);

    userInput.focus();
  }

  function updateProgress(current, total) {
    currentQuestionNum = current;
    totalQuestions = total;
    progressCounter.textContent = `Question ${current} of ${total}`;
    const pct = Math.min(100, Math.round((current / total) * 100));
    progressBarFill.style.width = `${pct}%`;
  }

  function renderCurriculum(concepts, activeIdx) {
    curriculumList.innerHTML = '';
    concepts.forEach((concept, idx) => {
      const item = document.createElement('div');
      item.className = 'curriculum-item';
      if (idx < activeIdx) {
        item.classList.add('completed');
        item.innerHTML = `<span class="curriculum-status-icon">✓</span> <span>${concept}</span>`;
      } else if (idx === activeIdx) {
        item.classList.add('active');
        item.innerHTML = `<span class="curriculum-status-icon">●</span> <span>${concept}</span>`;
      } else {
        item.innerHTML = `<span class="curriculum-status-icon">○</span> <span>${concept}</span>`;
      }
      curriculumList.appendChild(item);
    });
  }

  // 6. Messaging in Chat
  function appendStudentMessage(text) {
    const row = document.createElement('div');
    row.className = 'message-row student-row';

    const avatar = document.createElement('div');
    avatar.className = 'msg-avatar';
    avatar.textContent = sidebarStudentAvatar.textContent;

    const content = document.createElement('div');
    const author = document.createElement('div');
    author.className = 'msg-author';
    author.textContent = sidebarStudentName.textContent;

    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble';
    bubble.innerHTML = formatMarkdown(text);

    content.appendChild(author);
    content.appendChild(bubble);

    row.appendChild(avatar);
    row.appendChild(content);

    chatMessages.appendChild(row);
    scrollToBottom();
  }

  function appendTeacherMessage(text) {
    const row = document.createElement('div');
    row.className = 'message-row teacher-row';

    const avatar = document.createElement('div');
    avatar.className = 'msg-avatar';
    avatar.textContent = '👨‍🏫';

    const content = document.createElement('div');
    const author = document.createElement('div');
    author.className = 'msg-author';
    author.textContent = 'You (Teacher)';

    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble';
    bubble.textContent = text;

    content.appendChild(author);
    content.appendChild(bubble);

    row.appendChild(avatar);
    row.appendChild(content);

    chatMessages.appendChild(row);
    scrollToBottom();
  }

  function showTypingIndicator() {
    const typingRow = document.createElement('div');
    typingRow.id = 'typingIndicator';
    typingRow.className = 'typing-row';
    typingRow.innerHTML = `
      <span>Alex is synthesizing your explanation</span>
      <div class="typing-dots"><span></span><span></span><span></span></div>
    `;
    chatMessages.appendChild(typingRow);
    scrollToBottom();
  }

  function removeTypingIndicator() {
    const typing = document.getElementById('typingIndicator');
    if (typing) typing.remove();
  }

  function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  // Handle Input Auto-Grow and Keyboard Submit
  userInput.addEventListener('input', () => {
    userInput.style.height = 'auto';
    userInput.style.height = `${Math.min(140, userInput.scrollHeight)}px`;
    sendBtn.disabled = !userInput.value.trim() || isSending;
  });

  userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (userInput.value.trim() && !isSending) {
        submitTeacherResponse();
      }
    }
  });

  chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    if (userInput.value.trim() && !isSending) {
      submitTeacherResponse();
    }
  });

  async function submitTeacherResponse() {
    const text = userInput.value.trim();
    if (!text || isSending || !sessionId) return;

    isSending = true;
    sendBtn.disabled = true;
    userInput.value = '';
    userInput.style.height = 'auto';

    appendTeacherMessage(text);
    showTypingIndicator();

    try {
      const res = await fetch('/api/step', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          message: text,
        }),
      });
      const data = await res.json();
      removeTypingIndicator();

      if (!res.ok) throw new Error(data.error || 'Server error');

      appendStudentMessage(data.student_reply);

      if (data.turn_metric && data.turn_metric.student_state) {
        studentStateBadge.textContent = data.turn_metric.student_state;
      }

      if (data.current_concept) {
        currentTopicTitle.textContent = data.current_concept;
      }

      if (data.is_series_complete) {
        // Study session complete!
        updateProgress(totalQuestions, totalQuestions);
        renderCurriculum(currentDoc.concepts.slice(0, totalQuestions), totalQuestions);
        showReportModal(data.final_report || data.report_text, data.overall_score, data.grade);
      } else {
        const nextQ = data.question_number || (currentQuestionNum + 1);
        updateProgress(nextQ, totalQuestions);
        renderCurriculum(currentDoc.concepts.slice(0, totalQuestions), nextQ - 1);
      }
    } catch (err) {
      removeTypingIndicator();
      alert('Error sending answer: ' + err.message);
    } finally {
      isSending = false;
      sendBtn.disabled = !userInput.value.trim();
      userInput.focus();
    }
  }

  // Quick Suggestion Chips
  document.querySelectorAll('.chip-btn').forEach(chip => {
    chip.addEventListener('click', () => {
      const text = chip.dataset.text;
      userInput.value = text;
      userInput.dispatchEvent(new Event('input'));
      userInput.focus();
    });
  });

  // 7. Sidebar Commands
  btnViewReport.addEventListener('click', async () => {
    if (!sessionId) return;
    try {
      const res = await fetch('/api/report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to fetch report');
      showReportModal(data.final_report, data.overall_score, data.grade);
    } catch (err) {
      alert('Error fetching report: ' + err.message);
    }
  });

  btnConcludeEarly.addEventListener('click', () => {
    if (confirm('Conclude the study session now and view your performance report?')) {
      userInput.value = '/done';
      submitTeacherResponse();
    }
  });

  btnRetestQuick.addEventListener('click', () => {
    if (confirm('Restart this study series from Question 1?')) {
      retestSession();
    }
  });

  async function retestSession() {
    if (!sessionId) return;
    try {
      const res = await fetch('/api/retest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to restart');

      chatMessages.innerHTML = '';
      updateProgress(1, totalQuestions);
      renderCurriculum(currentDoc.concepts.slice(0, totalQuestions), 0);
      currentTopicTitle.textContent = data.current_concept || 'Topic 1';
      appendStudentMessage(data.student_opening);
      closeReportModal.click();
    } catch (err) {
      alert('Error restarting session: ' + err.message);
    }
  }

  // 8. Performance Report Modal
  function showReportModal(reportText, score, grade) {
    
    modalReportContent.innerHTML = '';
    
    // Confetti
    if (score >= 80) {
      fireConfetti();
    }

    const reportContainer = document.createElement('div');
    reportContainer.className = 'gamified-report';
    
    const displayScore = score !== undefined ? `${score.toFixed(1)}%` : '--';
    const displayGrade = grade || 'Completed';
    
    let badgesHtml = '';
    if (score >= 90) badgesHtml += '<span class="badge">🌟 Master Communicator</span>';
    if (score >= 80) badgesHtml += '<span class="badge">🧠 Deep Thinker</span>';
    badgesHtml += '<span class="badge">🔥 Feynman Scholar</span>';

    // Parse metrics
    const accuracyMatch = reportText ? reportText.match(/Scientific Accuracy:\s+([\d.]+)/) : null;
    const clarityMatch = reportText ? reportText.match(/Clarity & Simplicity:\s+([\d.]+)/) : null;
    const depthMatch = reportText ? reportText.match(/Explanation Depth:\s+([\d.]+)/) : null;
    const respMatch = reportText ? reportText.match(/Responsiveness:\s+([\d.]+)/) : null;
    
    const accuracy = accuracyMatch ? parseFloat(accuracyMatch[1]) : 0;
    const clarity = clarityMatch ? parseFloat(clarityMatch[1]) : 0;
    const depth = depthMatch ? parseFloat(depthMatch[1]) : 0;
    const resp = respMatch ? parseFloat(respMatch[1]) : 0;
    
    // Extract questions
    const qRegex = /\[(Q\d+)\]\s+(.*?)\s+:\s+([\d.]+)%\s+\[(.*?)\]/g;
    let qMatch;
    const questions = [];
    if (reportText) {
        while ((qMatch = qRegex.exec(reportText)) !== null) {
            questions.push({
                id: qMatch[1],
                topic: qMatch[2].trim(),
                score: parseFloat(qMatch[3]),
                status: qMatch[4]
            });
        }
    }

    let chartsHtml = '';
    if (accuracy || questions.length) {
      let excellent = 0, average = 0, poor = 0;
      questions.forEach(q => {
          if (q.score >= 80) excellent++;
          else if (q.score >= 50) average++;
          else poor++;
      });
      const totalQ = questions.length || 1;
      const pExc = (excellent / totalQ) * 100;
      const pAvg = (average / totalQ) * 100;
      const pPoor = (poor / totalQ) * 100;

      chartsHtml = `
        <div class="report-charts" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 30px; animation: popIn 0.8s ease forwards; opacity: 0; animation-delay: 0.3s;">
          <style>
            @keyframes slideWidth { from { width: 0; } }
            @keyframes fadeUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
            @keyframes drawPie { from { stroke-dashoffset: 100; } to { stroke-dashoffset: var(--target-offset); } }
          </style>
          
          <!-- Topic Mastery Breakdown (Pie Chart) -->
          <div class="chart-card" style="background: rgba(0,0,0,0.2); padding: 25px; border-radius: 12px; border: 1px solid var(--border-color); text-align: left; display: flex; flex-direction: column; align-items: center; justify-content: center;">
            <h3 style="margin-bottom: 20px; color: var(--text-muted); font-size: 13px; text-transform: uppercase; letter-spacing: 1px; align-self: flex-start; width: 100%;">Mastery Breakdown</h3>
            <div style="width: 150px; height: 150px; position: relative; animation: fadeUp 0.8s ease forwards; opacity: 0; animation-delay: 0.5s;">
              <svg viewBox="0 0 36 36" style="width: 100%; height: 100%; transform: rotate(-90deg); border-radius: 50%; box-shadow: 0 0 20px rgba(0,0,0,0.5); background: rgba(255,255,255,0.02);">
                <circle cx="18" cy="18" r="15.9155" fill="none" stroke="#ef4444" stroke-width="6" stroke-dasharray="${pPoor > 0 ? '100' : '0'} 100"></circle>
                <circle cx="18" cy="18" r="15.9155" fill="none" stroke="#f59e0b" stroke-width="6" stroke-dasharray="${pAvg} 100" stroke-dashoffset="-${pPoor}" style="--target-offset: -${pPoor};"></circle>
                <circle cx="18" cy="18" r="15.9155" fill="none" stroke="#10b981" stroke-width="6" stroke-dasharray="${pExc} 100" stroke-dashoffset="-${pPoor + pAvg}" style="--target-offset: -${pPoor + pAvg};"></circle>
              </svg>
              <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                <span style="font-size: 24px; font-weight: bold; color: var(--text-main);">${totalQ}</span>
                <span style="font-size: 10px; color: var(--text-muted); text-transform: uppercase;">Topics</span>
              </div>
            </div>
            <div style="display: flex; gap: 15px; margin-top: 25px; font-size: 12px; animation: fadeUp 0.5s ease forwards; opacity: 0; animation-delay: 0.7s; color: var(--text-main);">
              <div style="display: flex; align-items: center; gap: 6px;"><span style="width:10px;height:10px;border-radius:50%;background:#10b981;box-shadow:0 0 5px #10b981;"></span> Mastered</div>
              <div style="display: flex; align-items: center; gap: 6px;"><span style="width:10px;height:10px;border-radius:50%;background:#f59e0b;box-shadow:0 0 5px #f59e0b;"></span> OK</div>
              <div style="display: flex; align-items: center; gap: 6px;"><span style="width:10px;height:10px;border-radius:50%;background:#ef4444;box-shadow:0 0 5px #ef4444;"></span> Poor</div>
            </div>
          </div>

          <!-- Metrics Bar Chart -->
          <div class="chart-card" style="background: rgba(0,0,0,0.2); padding: 25px; border-radius: 12px; border: 1px solid var(--border-color); text-align: left;">
            <h3 style="margin-bottom: 20px; color: var(--text-muted); font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">Core Competencies</h3>
            <div style="display: flex; flex-direction: column; gap: 18px;">
              ${[
                { label: 'Scientific Accuracy', val: accuracy, color: '#3b82f6' },
                { label: 'Clarity & Simplicity', val: clarity, color: '#10b981' },
                { label: 'Explanation Depth', val: depth, color: '#f59e0b' },
                { label: 'Responsiveness', val: resp, color: '#8b5cf6' }
              ].map((m, i) => `
                <div style="animation: fadeUp 0.5s ease forwards; opacity: 0; animation-delay: ${(i*0.1) + 0.8}s;">
                  <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 14px;">
                    <span>${m.label}</span>
                    <strong style="color: ${m.color}">${m.val} / 10</strong>
                  </div>
                  <div style="width: 100%; height: 10px; background: rgba(255,255,255,0.05); border-radius: 5px; overflow: hidden; box-shadow: inset 0 1px 3px rgba(0,0,0,0.3);">
                    <div style="height: 100%; background: ${m.color}; border-radius: 5px; width: ${m.val * 10}%; animation: slideWidth 1s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards; animation-delay: ${(i*0.1) + 0.9}s; transform-origin: left;"></div>
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
          
          <!-- Progression Timeline -->
          <div class="chart-card" style="background: rgba(0,0,0,0.2); padding: 25px; border-radius: 12px; border: 1px solid var(--border-color); text-align: left; grid-column: 1 / -1;">
            <h3 style="margin-bottom: 20px; color: var(--text-muted); font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">Topic Progression</h3>
            <div style="display: flex; flex-direction: column; gap: 15px; position: relative;">
              <div style="position: absolute; left: 19px; top: 20px; bottom: 20px; width: 2px; background: rgba(255,255,255,0.05);"></div>
              ${questions.map((q, i) => `
                <div style="display: flex; align-items: center; gap: 20px; animation: fadeUp 0.5s ease forwards; opacity: 0; animation-delay: ${(i*0.1) + 1.2}s; position: relative; z-index: 1;">
                  <div style="min-width: 40px; height: 40px; border-radius: 50%; background: var(--bg-main); color: ${q.score >= 80 ? '#10b981' : (q.score >= 50 ? '#f59e0b' : '#ef4444')}; display: flex; align-items: center; justify-content: center; font-weight: bold; border: 2px solid currentColor; box-shadow: 0 0 10px rgba(0,0,0,0.5);">${q.id.replace('Q', '')}</div>
                  <div style="flex: 1;">
                    <div style="font-weight: 600; margin-bottom: 4px; color: #fff;">${q.topic}</div>
                    <div style="font-size: 12px; color: var(--text-muted); display: flex; align-items: center; gap: 8px;">
                      <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: ${q.score >= 80 ? '#10b981' : (q.score >= 50 ? '#f59e0b' : '#ef4444')};"></span>
                      ${q.status}
                    </div>
                  </div>
                  <div style="font-size: 18px; font-weight: 700; color: ${q.score >= 80 ? '#10b981' : (q.score >= 50 ? '#f59e0b' : '#ef4444')};">
                    ${Math.round(q.score)}%
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
        </div>
      `;
    }

    reportContainer.innerHTML = `
      <div class="grade-container" style="animation: popIn 0.8s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;">
        <h2 style="color: var(--text-muted); font-size: 16px; margin-bottom: 8px; letter-spacing: 2px;">OVERALL MASTERY</h2>
        <div class="giant-grade">${displayGrade}</div>
        <div style="font-size: 24px; font-weight: 700; margin-top: 8px;">${displayScore}</div>
      </div>
      <div class="badges-container" style="animation: popIn 0.6s ease forwards; animation-delay: 0.1s; opacity: 0; transform: scale(0.9);">
        ${badgesHtml}
      </div>
      ${chartsHtml}
      
      <!-- Hidden full raw report for copy pasting -->
      <pre class="raw-report-view" style="display: none;">${reportText || 'No report generated yet.'}</pre>
    `;
    modalReportContent.appendChild(reportContainer);

    reportModal.style.display = 'flex';
  }

  closeReportModal.addEventListener('click', () => {
    reportModal.style.display = 'none';
  });

  modalRetestBtn.addEventListener('click', () => {
    reportModal.style.display = 'none';
    retestSession();
  });

  modalCopyBtn.addEventListener('click', () => {
    const text = modalReportContent.querySelector('.raw-report-view')?.textContent || '';
    navigator.clipboard.writeText(text).then(() => {
      modalCopyBtn.textContent = '✓ Copied!';
      setTimeout(() => { modalCopyBtn.textContent = '📋 Copy Markdown Report'; }, 2000);
    });
  });

  modalNewDocBtn.addEventListener('click', () => {
    reportModal.style.display = 'none';
    resetToSetup();
  });

  resetSessionBtn.addEventListener('click', () => {
    if (confirm('Start over with a new document?')) {
      resetToSetup();
    }
  });

  function resetToSetup() {
    sessionId = null;
    currentDoc = null;
    chatScreen.style.display = 'none';
    setupScreen.style.display = 'block';
    resetSessionBtn.style.display = 'none';
    changeFileBtn.click();
  }

  function formatMarkdown(text) {
    if (!text) return '';
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n\n/g, '<br><br>')
      .replace(/\n/g, '<br>');
  }

  // --- POMODORO LOGIC ---
  const pomodoroDisplay = document.getElementById('pomodoroDisplay');
  const btnPomodoroStart = document.getElementById('btnPomodoroStart');
  const btnPomodoroPause = document.getElementById('btnPomodoroPause');
  const btnPomodoroReset = document.getElementById('btnPomodoroReset');
  
  let pomodoroInterval = null;
  let pomodoroTimeLeft = 25 * 60; // 25 minutes in seconds

  function updatePomodoroDisplay() {
    if (!pomodoroDisplay) return;
    const minutes = Math.floor(pomodoroTimeLeft / 60);
    const seconds = pomodoroTimeLeft % 60;
    pomodoroDisplay.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  }

  if (btnPomodoroStart) {
    btnPomodoroStart.addEventListener('click', () => {
      if (pomodoroInterval) return; // already running
      pomodoroInterval = setInterval(() => {
        pomodoroTimeLeft--;
        if (pomodoroTimeLeft <= 0) {
          clearInterval(pomodoroInterval);
          pomodoroInterval = null;
          pomodoroTimeLeft = 0;
          alert("Pomodoro session complete! Take a break.");
        }
        updatePomodoroDisplay();
      }, 1000);
    });
  }

  if (btnPomodoroPause) {
    btnPomodoroPause.addEventListener('click', () => {
      clearInterval(pomodoroInterval);
      pomodoroInterval = null;
    });
  }

  if (btnPomodoroReset) {
    btnPomodoroReset.addEventListener('click', () => {
      clearInterval(pomodoroInterval);
      pomodoroInterval = null;
      pomodoroTimeLeft = 25 * 60;
      updatePomodoroDisplay();
    });
  }

  // --- TO DO LIST LOGIC ---
  const todoInput = document.getElementById('todoInput');
  const btnTodoAdd = document.getElementById('btnTodoAdd');
  const todoList = document.getElementById('todoList');

  function createTodoElement(text) {
    const li = document.createElement('li');
    li.style.display = 'flex';
    li.style.alignItems = 'center';
    li.style.justifyContent = 'space-between';
    li.style.padding = '12px 16px';
    li.style.background = 'var(--bg-main)';
    li.style.border = '1px solid var(--border)';
    li.style.borderRadius = 'var(--radius-sm)';
    li.style.color = 'var(--text-main)';

    const labelContainer = document.createElement('label');
    labelContainer.style.display = 'flex';
    labelContainer.style.alignItems = 'center';
    labelContainer.style.gap = '12px';
    labelContainer.style.cursor = 'pointer';
    labelContainer.style.flex = '1';

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.style.cursor = 'pointer';

    const span = document.createElement('span');
    span.textContent = text;
    span.style.transition = 'color 0.2s, text-decoration 0.2s';

    checkbox.addEventListener('change', () => {
      if (checkbox.checked) {
        span.style.textDecoration = 'line-through';
        span.style.color = 'var(--text-muted)';
      } else {
        span.style.textDecoration = 'none';
        span.style.color = 'var(--text-main)';
      }
    });

    labelContainer.appendChild(checkbox);
    labelContainer.appendChild(span);

    const deleteBtn = document.createElement('button');
    deleteBtn.textContent = '×';
    deleteBtn.style.background = 'transparent';
    deleteBtn.style.border = 'none';
    deleteBtn.style.color = 'var(--text-muted)';
    deleteBtn.style.fontSize = '20px';
    deleteBtn.style.cursor = 'pointer';
    deleteBtn.style.lineHeight = '1';

    deleteBtn.addEventListener('click', () => {
      li.remove();
    });

    li.appendChild(labelContainer);
    li.appendChild(deleteBtn);

    return li;
  }

  if (btnTodoAdd) {
    btnTodoAdd.addEventListener('click', () => {
      const text = todoInput.value.trim();
      if (text) {
        todoList.appendChild(createTodoElement(text));
        todoInput.value = '';
      }
    });
  }

  if (todoInput) {
    todoInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        btnTodoAdd.click();
      }
    });
  }

  // --- ASSESSMENT MODE ---
  const btnAssessmentMode = document.getElementById('btnAssessmentMode');
  const assessmentScreen = document.getElementById('assessmentScreen');
  const btnBackFromAssessment = document.getElementById('btnBackFromAssessment');
  const btnStartAssessment = document.getElementById('btnStartAssessment');
  const assessmentTopicInput = document.getElementById('assessmentTopicInput');
  const assessmentLibrarySelect = document.getElementById('assessmentLibrarySelect');
  const assessmentNumQuestions = document.getElementById('assessmentNumQuestions');
  const assessmentStartCard = document.getElementById('assessmentStartCard');
  const assessmentQuestionsCard = document.getElementById('assessmentQuestionsCard');
  const assessmentQuestionsList = document.getElementById('assessmentQuestionsList');
  const btnSubmitAssessment = document.getElementById('btnSubmitAssessment');
  const assessmentResultCard = document.getElementById('assessmentResultCard');
  const assessmentScoreDisplay = document.getElementById('assessmentScoreDisplay');

  let currentExamId = "";
  let currentExamQuestions = [];

  if (btnAssessmentMode) {
    btnAssessmentMode.addEventListener('click', async () => {
      landingScreen.style.display = 'none';
      assessmentScreen.style.display = 'block';
      assessmentStartCard.style.display = 'block';
      assessmentQuestionsCard.style.display = 'none';
      assessmentResultCard.style.display = 'none';
      
      // Load materials into the select dropdown
      try {
        const res = await fetch('/api/materials');
        const data = await res.json();
        assessmentLibrarySelect.innerHTML = '<option value="">-- Select Material --</option>';
        (data.materials || []).forEach(m => {
          const opt = document.createElement('option');
          opt.value = m.id;
          opt.textContent = m.file_name;
          assessmentLibrarySelect.appendChild(opt);
        });
      } catch (e) {
        console.error("Failed to load materials for assessment:", e);
      }
    });
  }

  if (btnBackFromAssessment) {
    btnBackFromAssessment.addEventListener('click', () => {
      assessmentScreen.style.display = 'none';
      landingScreen.style.display = 'block';
    });
  }

  if (btnStartAssessment) {
    btnStartAssessment.addEventListener('click', async () => {
      const topic = assessmentTopicInput.value.trim();
      const material_id = assessmentLibrarySelect.value;
      const numQ = parseInt(assessmentNumQuestions.value) || 3;
      
      if (!topic && !material_id) {
        return alert("Please enter a topic OR select a material.");
      }
      
      btnStartAssessment.disabled = true;
      btnStartAssessment.textContent = "Researching & Generating Exam...";

      try {
        const res = await fetch('/api/exam/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ topic, material_id, num_questions: numQ })
        });
        const data = await res.json();
        
        if (data.error) {
          alert("Error: " + data.error);
        } else if (data.questions) {
          currentExamId = data.exam_id;
          currentExamQuestions = data.questions;
          
          assessmentStartCard.style.display = 'none';
          assessmentQuestionsCard.style.display = 'block';
          
          assessmentQuestionsList.innerHTML = '';
          currentExamQuestions.forEach((q, idx) => {
            const block = document.createElement('div');
            block.style.marginBottom = '20px';
            block.innerHTML = `
              <p style="font-weight: 600; margin-bottom: 8px;">Q${idx + 1}: ${q.question}</p>
              <textarea id="examAnswer_${q.id}" class="topic-text-input" style="width: 100%; min-height: 80px;" placeholder="Your answer..."></textarea>
            `;
            assessmentQuestionsList.appendChild(block);
          });
        }
      } catch (e) {
        alert("Failed to start exam: " + e);
      } finally {
        btnStartAssessment.disabled = false;
        btnStartAssessment.textContent = "Generate Exam";
      }
    });
  }

  if (btnSubmitAssessment) {
    btnSubmitAssessment.addEventListener('click', async () => {
      const answers = {};
      currentExamQuestions.forEach(q => {
        answers[q.id] = document.getElementById(`examAnswer_${q.id}`).value.trim();
      });

      btnSubmitAssessment.disabled = true;
      btnSubmitAssessment.textContent = "Grading via AI...";

      try {
        const res = await fetch('/api/exam/grade', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ exam_id: currentExamId, answers })
        });
        const data = await res.json();
        
        if (data.error) {
          alert("Error: " + data.error);
        } else if (data.results) {
          assessmentQuestionsCard.style.display = 'none';
          assessmentResultCard.style.display = 'block';
          
          let resultsHtml = `<div style="font-size: 24px; font-weight: bold; margin-bottom: 16px;">Total Score: ${data.percentage}/100</div>`;
          resultsHtml += `<p style="margin-bottom: 24px;"><strong>Overall Feedback:</strong> ${data.overall_feedback}</p>`;
          
          data.results.forEach((r, idx) => {
            resultsHtml += `
              <div style="background: var(--bg-surface); padding: 16px; border-radius: 8px; margin-bottom: 16px; border: 1px solid var(--border);">
                <h4>Q${idx + 1} Score: ${r.score}/10</h4>
                <p><strong>Feedback:</strong> ${r.feedback}</p>
                <div style="font-size: 0.9em; margin-top: 8px;">
                  <strong style="color: #10b981;">Hits:</strong> ${r.keypoints_hit.join(', ') || 'None'}<br/>
                  <strong style="color: #ef4444;">Missed:</strong> ${r.keypoints_missed.join(', ') || 'None'}
                </div>
              </div>
            `;
          });
          
          assessmentScoreDisplay.innerHTML = resultsHtml;
        }
      } catch (e) {
        alert("Failed to submit exam: " + e);
      } finally {
        btnSubmitAssessment.disabled = false;
        btnSubmitAssessment.textContent = "Submit Answers";
      }
    });
  }

  // --- MOBBIN CATEGORY FILTERS ---
  const mobbinPills = document.querySelectorAll('#mobbinFilters .mobbin-pill');
  const dashboardReportsSection = document.getElementById('dashboardReportsSection');
  const sectionCoreLearning = document.getElementById('sectionCoreLearning');
  const sectionProductivity = document.getElementById('sectionProductivity');
  const sectionReportsDetails = document.getElementById('sectionReportsDetails');
  const btnJumpToAssessmentFromReports = document.getElementById('btnJumpToAssessmentFromReports');

  if (mobbinPills.length > 0) {
    mobbinPills.forEach(pill => {
      pill.addEventListener('click', () => {
        // 1. Update active pill visual state
        mobbinPills.forEach(p => p.classList.remove('active'));
        pill.classList.add('active');

        const filter = pill.getAttribute('data-filter') || 'all';

        // 2. Filter sections and cards smoothly
        if (filter === 'all') {
          if (dashboardReportsSection) dashboardReportsSection.style.display = 'block';
          if (sectionCoreLearning) {
            sectionCoreLearning.style.display = 'block';
            sectionCoreLearning.querySelectorAll('.mobbin-card').forEach(c => c.style.display = 'flex');
          }
          if (sectionProductivity) {
            sectionProductivity.style.display = 'block';
            sectionProductivity.querySelectorAll('.mobbin-card').forEach(c => c.style.display = 'flex');
          }
          if (sectionReportsDetails) sectionReportsDetails.style.display = 'none';
        } else if (filter === 'study') {
          if (dashboardReportsSection) dashboardReportsSection.style.display = 'none';
          if (sectionProductivity) sectionProductivity.style.display = 'none';
          if (sectionReportsDetails) sectionReportsDetails.style.display = 'none';
          if (sectionCoreLearning) {
            sectionCoreLearning.style.display = 'block';
            sectionCoreLearning.querySelectorAll('.mobbin-card').forEach(c => {
              const cat = c.getAttribute('data-category') || '';
              c.style.display = cat.includes('study') ? 'flex' : 'none';
            });
          }
        } else if (filter === 'productivity') {
          if (dashboardReportsSection) dashboardReportsSection.style.display = 'none';
          if (sectionCoreLearning) sectionCoreLearning.style.display = 'none';
          if (sectionReportsDetails) sectionReportsDetails.style.display = 'none';
          if (sectionProductivity) {
            sectionProductivity.style.display = 'block';
            sectionProductivity.querySelectorAll('.mobbin-card').forEach(c => c.style.display = 'flex');
          }
        } else if (filter === 'assessments') {
          if (dashboardReportsSection) dashboardReportsSection.style.display = 'none';
          if (sectionProductivity) sectionProductivity.style.display = 'none';
          if (sectionReportsDetails) sectionReportsDetails.style.display = 'none';
          if (sectionCoreLearning) {
            sectionCoreLearning.style.display = 'block';
            sectionCoreLearning.querySelectorAll('.mobbin-card').forEach(c => {
              const cat = c.getAttribute('data-category') || '';
              c.style.display = cat.includes('assessments') ? 'flex' : 'none';
            });
          }
        } else if (filter === 'reports') {
          if (dashboardReportsSection) dashboardReportsSection.style.display = 'block';
          if (sectionCoreLearning) sectionCoreLearning.style.display = 'none';
          if (sectionProductivity) sectionProductivity.style.display = 'none';
          if (sectionReportsDetails) sectionReportsDetails.style.display = 'block';
        }
      });
    });
  }

  if (btnJumpToAssessmentFromReports) {
    btnJumpToAssessmentFromReports.addEventListener('click', () => {
      if (btnAssessmentMode) btnAssessmentMode.click();
    });
  }

});
