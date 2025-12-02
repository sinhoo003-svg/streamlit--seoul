<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>초등 영어 튜터 챗봇 (Sinu)</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Inter Font -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', sans-serif;
            background-color: #eef2ff;
        }
        .chat-bubble-koni {
            background-color: #cffafe;
            border-top-left-radius: 25px !important; 
            border-top-right-radius: 25px !important;
            border-bottom-right-radius: 25px !important;
            border-bottom-left-radius: 10px !important;
            max-width: 85%;
            align-self: flex-start;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        .chat-bubble-user {
            background-color: #6366f1;
            color: white;
            border-top-left-radius: 25px !important;
            border-top-right-radius: 25px !important;
            border-bottom-right-radius: 10px !important;
            border-bottom-left-radius: 25px !important;
            max-width: 85%;
            align-self: flex-end;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        /* Custom scrollbar for chat history */
        #chat-history {
            scrollbar-width: thin;
            scrollbar-color: #a78bfa #f3f4f6;
        }
        #chat-history::-webkit-scrollbar {
            width: 8px;
        }
        #chat-history::-webkit-scrollbar-thumb {
            background-color: #a78bfa;
            border-radius: 4px;
        }
        #chat-history::-webkit-scrollbar-track {
            background-color: #f3f4f6;
        }
        .option-button {
            transition: all 0.2s ease-in-out;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border: 2px solid transparent;
        }
        .option-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 10px rgba(0,0,0,0.2);
            border-color: #8b5cf6;
        }
        .results-page-container {
            min-height: 100vh;
        }
        /* Style for the help button */
        #help-button {
            background-color: #f87171;
        }
        #help-button:hover {
            background-color: #ef4444;
        }
    </style>
</head>
<body class="flex flex-col min-h-screen p-4 sm:p-6 md:p-8">

    <!-- Main Container -->
    <div class="flex flex-col flex-grow w-full max-w-4xl mx-auto bg-white rounded-2xl shadow-2xl overflow-hidden" id="main-app-container">
        
        <!-- Header -->
        <header class="p-4 sm:p-6 bg-indigo-500 text-white shadow-lg flex justify-between items-center" id="app-header">
            <h1 class="text-2xl sm:text-3xl font-extrabold flex items-center">
                <span class="mr-2 text-3xl">🌟</span> Sinu 영어 튜터링 시간!
            </h1>
            <p class="text-sm opacity-90 mt-1 hidden sm:block">신나는 "좋아하는 과목" 대화 연습! 😊</p>
        </header>

        <!-- Chat History -->
        <main id="chat-history" class="flex-grow p-4 sm:p-6 space-y-5 overflow-y-auto">
            <!-- Initial Message from Sinu -->
            <div class="flex justify-start">
                <div class="p-4 chat-bubble-koni">
                    <p class="font-bold text-indigo-700">Sinu ⭐</p>
                    <p class="mt-1">Hello! I'm Sinu, your English tutor. Nice to meet you! 😊 오늘 배운 내용을 복습 퀴즈로 먼저 확인해보자! 준비됐니? (Are you ready?)</p>
                </div>
            </div>
            <!-- Loading indicator placeholder -->
            <div id="loading-indicator" class="hidden flex justify-start">
                <div class="p-3 bg-gray-100 text-gray-500 rounded-lg shadow-inner">
                    <p>Sinu가 생각 중이야... 잠시만 기다려줘! 💡</p>
                </div>
            </div>
            <!-- Dynamic Report Content will replace this area -->
        </main>

        <!-- Input Area and Options (Combined) -->
        <div class="p-4 sm:p-6 border-t border-indigo-200 bg-indigo-50 flex flex-col space-y-4" id="input-control-area">
            <!-- Dynamic Button Container (for quiz options) -->
            <div id="option-container" class="flex flex-col space-y-2 sm:flex-row sm:space-y-0 sm:space-x-3"></div>

            <div class="flex items-center space-x-3">
                <!-- New help button: Visible only in conversation mode and when no quiz options are present -->
                <button id="help-button" 
                        class="p-3 bg-red-500 hover:bg-red-600 text-white font-bold rounded-xl shadow-lg transition duration-150 ease-in-out hidden disabled:opacity-50 text-sm whitespace-nowrap">
                    모르겠어요 🇰🇷
                </button>
                
                <input type="text" id="user-input" placeholder="여기에 영어로 답변을 입력해 주세요!"
                       class="flex-grow p-3 border-2 border-indigo-300 rounded-xl focus:ring-indigo-500 focus:border-indigo-500 text-base shadow-md">
                <button id="send-button"
                        class="p-3 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl shadow-lg transition duration-150 ease-in-out disabled:opacity-50">
                    Send
                </button>
            </div>
        </div>
    </div>

    <!-- JavaScript for Chatbot Logic -->
    <script type="module">
        // Import necessary Firebase modules
        import { initializeApp } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-app.js";
        import { getAuth, signInAnonymously, signInWithCustomToken } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-auth.js";
        import { setLogLevel } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-firestore.js";
        
        // --- Firebase Setup (Required for Canvas Environment) ---
        setLogLevel('Debug');

        const firebaseConfig = JSON.parse(typeof __firebase_config !== 'undefined' ? __firebase_config : '{}');
        const __initial_auth_token = typeof window.__initial_auth_token !== 'undefined' ? window.__initial_auth_token : undefined;

        let auth;
        let isAuthReady = false;

        if (Object.keys(firebaseConfig).length > 0) {
            const app = initializeApp(firebaseConfig);
            auth = getAuth(app);

            async function authenticate() {
                try {
                    if (__initial_auth_token) {
                        await signInWithCustomToken(auth, __initial_auth_token);
                    } else {
                        await signInAnonymously(auth);
                    }
                    console.log("Firebase Authentication successful.");
                    isAuthReady = true;
                } catch (error) {
                    console.error("Firebase Auth Error:", error);
                }
            }
            authenticate();
        } else {
            console.warn("Firebase config not found. Running in standalone mode.");
            isAuthReady = true; 
        }

        // --- Chatbot Logic ---
        
        const API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent";
        const apiKey = ""; 

        const chatHistoryElement = document.getElementById('chat-history');
        const userInput = document.getElementById('user-input');
        const sendButton = document.getElementById('send-button');
        const loadingIndicator = document.getElementById('loading-indicator');
        const inputControlArea = document.getElementById('input-control-area');
        const mainAppContainer = document.getElementById('main-app-container');
        const optionContainer = document.getElementById('option-container'); 
        const helpButton = document.getElementById('help-button'); // Get the new help button

        // Global State for Phase Tracking
        let isConversationMode = false;
        let finalReportText = null; // Stores the AI-generated report text

        // Function to update help button visibility
        function updateHelpButtonVisibility() {
            const isQuizActive = optionContainer.children.length > 0;
            const isReportActive = mainAppContainer.querySelector('.results-page-container');
            
            // Show help button only if in conversation mode (Phase 2) and no other interactive element is present
            if (isConversationMode && !isQuizActive && !isReportActive) {
                helpButton.classList.remove('hidden');
            } else {
                helpButton.classList.add('hidden');
            }
        }

        // System Instruction: Updated tutor name to 'Sinu' and symbol to '⭐'
        const systemInstruction = {
            parts: [{
                text: "You are 'Sinu', a friendly, encouraging English tutor for elementary students. Use a soft, positive tone in all messages. Use Korean when giving instructions, encouragement, or clarity checks, and use English for core questions and feedback. Use friendly emojis (like 😊, ✨, 📚, 💡) in your responses." +
                      "Your goal is to guide the student through three phases: 1. Quiz (Initial Review), 2. Conversation (Free Practice), and 3. Final Report. " +
                      "Phase 1 (Initial 4 turns): Immediately start the quiz after the initial greeting/first user input. Announce the quiz in Korean. Ask 4 alternating simple quiz questions. Question types MUST cover: 1) Korean subject name -> English, 2) English subject name -> Korean, 3) Question Pattern (e.g., '좋아하는 과목을 묻는 영어 표현은?'), 4) Statement Pattern (e.g., ''나는 미술을 좋아해' 영어 표현은?'). " +
                      "Crucial Rule for Quiz Questions (Phase 1): You MUST output the question followed by the exact marker `##OPTIONS##` and a pipe-separated list of 3 distinct subject options or phrase options (one correct, two incorrect). Example: `좋아하는 과목을 묻는 영어 표현은? ##OPTIONS##: What subject do you like? | What is your favorite subject? | What's your name?`. Do NOT send any other message until the student responds. " +
                      "Phase 2 (Next 4 turns): After the 4th quiz question is answered, announce the transition to free conversation in Korean (e.g., 'Great job! 퀴즈 잘했어! 이제 자유 대화를 해보자. What is your favorite subject?'). " +
                      "Crucial Rule for Sentence Completion (Phase 2): If the student replies with a single word or a short, incomplete phrase (e.g., 'Math', 'P.E.', 'like English'), you MUST complete the sentence for them (e.g., 'Ah, you mean 'My favorite subject is Math.' That's awesome!'). You must track internally how many times you provided this sentence completion guidance. If the student sends the special command 'ACTION: NEED SUBJECT NAME HELP', you must respond in Korean asking '무슨 과목에 대해 이야기하고 싶니? 한국어로 말해줘. (What subject do you want to talk about? Tell me in Korean.)'. If the student replies with a Korean subject name immediately following this Korean prompt, you MUST provide the English word for the subject and then say '이제 너가 한번 써봐! (Now, you try writing it!)' in a friendly, encouraging tone. Do NOT switch to the final report until the 8th turn is completed." +
                      "Phase 3 (Final Output): After the 4th conversation turn in Phase 2, generate a single, comprehensive report starting with the exact marker '## FINAL REPORT ##'. This report MUST be written primarily in Korean and include: 1) A confirmation of the student's favorite subject from Phase 2. 2) A summary of the quiz performance from Phase 1 (e.g., '총 4문제 중 3문제를 맞혔습니다.'). 3) A specific section for Sentence Completion Guidance based on your internal tracking (e.g., '자유 대화 중 문장 완성 지도가 2회 제공되었습니다.'). 4) A concluding encouraging remark to the student. Do NOT send any other message after the report. You can use brief Korean sentences for instructions, encouragement, or to clarify a quiz question to help the student understand easily."
            }]
        };

        let conversationHistory = [
            // Updated tutor name
            { role: "model", parts: [{ text: "Hello! I'm Sinu, your English tutor. Nice to meet you! 😊 오늘 배운 내용을 복습 퀴즈로 먼저 확인해보자! 준비됐니? (Are you ready?)" }] }
        ];

        // --- Final Report Renderer Function ---
        function renderFinalReport(reportText) {
            // 1. Extract Data using Regex
            const quizMatch = reportText.match(/총 (\d+)문제 중 (\d+)문제를 맞혔습니다/);
            const guidanceMatch = reportText.match(/문장 완성 지도가 (\d+)회 제공되었습니다/);

            const totalQuestions = quizMatch ? parseInt(quizMatch[1]) : 4;
            const correctAnswers = quizMatch ? parseInt(quizMatch[2]) : 0;
            const guidanceCount = guidanceMatch ? parseInt(guidanceMatch[1]) : 0;
            
            // Clean up report text, replacing the markers with a newline for cleaner presentation
            const remarkText = reportText.replace(/## FINAL REPORT ##|\n총 \d+문제 중 \d+문제를 맞혔습니다\./g, '')
                                         .replace(/\n자유 대화 중 문장 완성 지도가 \d+회 제공되었습니다\./g, '')
                                         .trim();

            // 2. Prepare UI for Report View
            mainAppContainer.innerHTML = '';
            mainAppContainer.classList.remove('overflow-hidden', 'flex-col', 'flex-grow');
            mainAppContainer.classList.add('justify-center', 'items-center', 'p-6', 'results-page-container', 'flex');
            document.body.classList.remove('flex-col');
            document.body.classList.add('flex', 'justify-center', 'items-center');
            
            // 3. Build the Results Card
            const resultsCard = document.createElement('div');
            resultsCard.className = 'w-full max-w-2xl bg-white rounded-2xl shadow-2xl p-6 sm:p-10 text-center border-4 border-indigo-400';
            
            // Calculate percentage for chart bar
            const quizPercent = (correctAnswers / totalQuestions) * 100;
            
            // Title & Student ID
            resultsCard.innerHTML = `
                <h2 class="text-4xl font-extrabold text-indigo-600 mb-2">🎉 학습 완료 보고서! ✨</h2>
                <p class="text-gray-600 mb-6 font-semibold">Sinu 튜터와의 신나는 수업 결과를 확인하세요!</p>
                <div class="text-xs text-gray-400 mb-6">Student ID: ${auth.currentUser?.uid || 'N/A'}</div>

                <div class="space-y-6">
                    <!-- Quiz Result Card (with Chart) -->
                    <div class="p-5 bg-purple-50 rounded-xl border-2 border-purple-300 shadow-lg">
                        <h3 class="text-xl font-bold text-purple-700 mb-4 flex items-center justify-center">📚 퀴즈 정답률</h3>
                        <p class="text-5xl font-extrabold text-purple-500 mb-3">${correctAnswers} / ${totalQuestions} 문제</p>
                        <div class="w-full h-8 bg-gray-200 rounded-full overflow-hidden mt-4">
                            <div class="h-full bg-green-500 transition-all duration-1000 ease-out flex items-center justify-center text-sm font-bold text-white shadow-inner" 
                                style="width: ${quizPercent}%;">
                                정답률: ${quizPercent.toFixed(0)}%
                            </div>
                        </div>
                    </div>

                    <!-- Guidance Result Card -->
                    <div class="p-5 bg-yellow-50 rounded-xl border-2 border-yellow-300 shadow-lg">
                        <h3 class="text-xl font-bold text-yellow-700 mb-3 flex items-center justify-center">💡 문장 완성 지도 횟수</h3>
                        <p class="text-5xl font-extrabold text-yellow-500">${guidanceCount} 회</p>
                        <p class="text-sm text-gray-500 mt-2">횟수가 낮을수록 유창하게 문장을 구사했습니다. (자유 대화 기준)</p>
                    </div>

                    <!-- AI's Remark -->
                    <div class="p-4 bg-gray-100 rounded-xl border border-gray-300 text-left shadow-inner">
                        <h3 class="text-lg font-bold text-gray-700 mb-2 flex items-center">⭐ Sinu의 튜터링 코멘트</h3>
                        <p class="text-gray-700 whitespace-pre-wrap leading-relaxed">${remarkText}</p>
                    </div>
                </div>
                
                <!-- Teacher Action -->
                <div class="mt-8">
                    <h3 class="text-xl font-bold text-gray-700 mb-3 flex items-center justify-center">📧 교사에게 결과 전송</h3>
                    <button id="transmit-final-button" class="w-full py-4 bg-pink-500 hover:bg-pink-600 text-white font-bold text-xl rounded-xl shadow-xl transition duration-200 disabled:opacity-50">
                        결과 전송하기
                    </button>
                    <p id="completion-message" class="text-green-600 font-extrabold text-xl mt-4 hidden flex items-center justify-center">
                        ✅ 전송 완료! 오늘 수업은 여기서 마무리합니다. 안녕! 👋
                    </p>
                </div>
            `;

            mainAppContainer.appendChild(resultsCard);

            // 4. Attach event listener to the Transmit button
            document.getElementById('transmit-final-button').onclick = (e) => {
                e.target.disabled = true;
                e.target.textContent = '전송 중... 🚀';
                
                // Simulate API call or transmission delay
                setTimeout(() => {
                    e.target.classList.remove('bg-pink-500', 'hover:bg-pink-600');
                    e.target.classList.add('bg-gray-400');
                    e.target.textContent = '전송 완료! 💌';
                    
                    // Show completion message
                    document.getElementById('completion-message').classList.remove('hidden');
                }, 1500); // 1.5 second delay for effect
            };
        }

        // Function to create and display clickable buttons
        function displayOptions(optionsText) {
            optionContainer.innerHTML = ''; // Clear previous options
            const options = optionsText.split('|').map(o => o.trim()).filter(o => o.length > 0);
            
            options.forEach(option => {
                const button = document.createElement('button');
                button.textContent = option;
                button.className = 'option-button flex-grow p-3 bg-indigo-500 hover:bg-indigo-600 text-white font-bold rounded-xl shadow-lg transition duration-150 ease-in-out text-base disabled:opacity-50';
                button.onclick = () => handleOptionClick(option);
                optionContainer.appendChild(button);
            });

            // Disable main text input and send button
            userInput.disabled = true;
            sendButton.disabled = true;
            userInput.placeholder = '버튼을 클릭하여 답변해주세요. 👆';
            
            chatHistoryElement.scrollTop = chatHistoryElement.scrollHeight; // Auto-scroll to show options context
            updateHelpButtonVisibility(); // Update help button visibility
        }

        // Function to handle button click
        function handleOptionClick(selectedOption) {
            optionContainer.innerHTML = ''; // Hide buttons
            userInput.disabled = false;
            sendButton.disabled = false;
            userInput.placeholder = '여기에 영어로 답변을 입력해 주세요!';
            
            // Simulate user sending the clicked text
            handleSend(selectedOption, true); 
            updateHelpButtonVisibility(); // Update help button visibility
        }

        // Function to handle "I don't know" button click
        function handleUnknownSubjectClick() {
            // Send a special, hidden command to the AI
            handleSend("ACTION: NEED SUBJECT NAME HELP", true);
            updateHelpButtonVisibility(); // Hide help button while waiting for AI response
        }
        
        // Attach event listener to the new button
        helpButton.addEventListener('click', handleUnknownSubjectClick);


        function createMessageElement(text, role) {
            
            // 1. Check for Phase transition and update state
            if (role === 'model' && text.includes('이제 자유 대화를 해보자.')) {
                isConversationMode = true;
            }
            
            // 2. Standard Message Rendering & Option Check
            const optionMarker = '##OPTIONS##:';
            let messageContent = text;
            let optionsText = null;

            if (role === 'model' && text.includes(optionMarker)) {
                const parts = text.split(optionMarker);
                messageContent = parts[0].trim();
                optionsText = parts[1].trim();
            }

            const messageWrapper = document.createElement('div');
            messageWrapper.className = `flex ${role === 'user' ? 'justify-end' : 'justify-start'}`;
            
            const messageBubble = document.createElement('div');
            messageBubble.className = `p-4 mt-2 ${role === 'user' ? 'chat-bubble-user' : 'chat-bubble-koni'}`;
            
            if (role === 'model') {
                const nameTag = document.createElement('p');
                nameTag.className = 'font-bold text-indigo-700';
                nameTag.textContent = 'Sinu ⭐';
                messageBubble.appendChild(nameTag);
            }

            const messageText = document.createElement('p');
            messageText.className = 'mt-1 whitespace-pre-wrap';
            messageText.textContent = messageContent;
            messageBubble.appendChild(messageText);
            
            messageWrapper.appendChild(messageBubble);
            chatHistoryElement.appendChild(messageWrapper);
            
            // 4. Display options if marker was present
            if (optionsText) {
                displayOptions(optionsText);
            }
            
            chatHistoryElement.scrollTop = chatHistoryElement.scrollHeight;
            updateHelpButtonVisibility(); // Update help button visibility after rendering
        }

        function toggleLoading(isLoading) {
            // Only disable input/send if options are not currently displayed
            if (optionContainer.children.length === 0) {
                sendButton.disabled = isLoading;
                userInput.disabled = isLoading;
            }
            loadingIndicator.classList.toggle('hidden', !isLoading);
            if (isLoading) {
                chatHistoryElement.scrollTop = chatHistoryElement.scrollHeight;
            }
        }

        async function fetchAIResponse(userText) {
            const userMessage = { role: "user", parts: [{ text: userText }] };
            conversationHistory.push(userMessage);

            const payload = {
                contents: conversationHistory,
                systemInstruction: systemInstruction
            };

            const maxRetries = 3;
            let currentRetry = 0;
            let aiText = "Sorry, I can't talk right now. Can you try again?";

            while (currentRetry < maxRetries) {
                try {
                    const response = await fetch(`${API_URL}?key=${apiKey}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });

                    if (!response.ok) {
                        const errorBody = await response.json();
                        console.error("API Error:", response.status, errorBody);
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }

                    const result = await response.json();
                    
                    if (result.candidates && result.candidates.length > 0 && result.candidates[0].content && result.candidates[0].content.parts) {
                        aiText = result.candidates[0].content.parts[0].text;
                        break;
                    } else {
                        throw new Error("Invalid response structure from API.");
                    }
                } catch (error) {
                    console.error(`Attempt ${currentRetry + 1} failed:`, error);
                    currentRetry++;
                    if (currentRetry < maxRetries) {
                        const delay = Math.pow(2, currentRetry) * 1000;
                        await new Promise(resolve => setTimeout(resolve, delay));
                    }
                }
            }
            
            // --- NEW LOGIC: Intercept Final Report ---
            if (aiText.startsWith('## FINAL REPORT ##')) {
                finalReportText = aiText;
                
                // 1. Manually create Sinu's final instruction message bubble (NOT logged to conversationHistory)
                const completionMessage = "수업이 끝났어요! 🎊 대화 내용과 퀴즈 결과를 정리했어요. 아래 버튼을 눌러서 학습 결과를 확인해 보세요! 👇";
                
                const finalMessageWrapper = document.createElement('div');
                finalMessageWrapper.className = `flex justify-start mt-4`;
                const finalMessageBubble = document.createElement('div');
                finalMessageBubble.className = 'p-4 chat-bubble-koni';
                finalMessageBubble.innerHTML = `<p class="font-bold text-indigo-700">Sinu ⭐</p><p class="mt-1">${completionMessage}</p>`;
                finalMessageWrapper.appendChild(finalMessageBubble);
                chatHistoryElement.appendChild(finalMessageWrapper);

                // 2. Add the result button to the chat history
                const resultButtonWrapper = document.createElement('div');
                resultButtonWrapper.className = 'flex justify-center mt-6 p-4 w-full';
                const resultButton = document.createElement('button');
                resultButton.textContent = '📊 결과 확인하기 (최종 보고서)';
                resultButton.className = 'py-3 px-8 bg-pink-500 hover:bg-pink-600 text-white font-bold text-xl rounded-xl shadow-xl transition duration-200';
                resultButton.onclick = () => renderFinalReport(finalReportText);
                
                resultButtonWrapper.appendChild(resultButton);
                chatHistoryElement.appendChild(resultButtonWrapper);

                // 3. Disable input controls permanently since the session is complete
                inputControlArea.style.display = 'none'; 
                chatHistoryElement.scrollTop = chatHistoryElement.scrollHeight;
                return; // Stop processing, the chat ends here.
            }
            // --- END NEW LOGIC ---

            conversationHistory.push({ role: "model", parts: [{ text: aiText }] });
            createMessageElement(aiText, 'model');
        }

        async function handleSend(predefinedText = null, isOptionClick = false) {
            const text = predefinedText !== null ? predefinedText : userInput.value.trim();
            if (!text) return;

            // 1. Display user message (only if not an option click, or if we want to show the clicked text)
            if (predefinedText !== null || !isOptionClick) {
                 createMessageElement(text, 'user');
            }
           
            userInput.value = '';

            // 2. Start loading and disable input
            toggleLoading(true);

            // 3. Get AI response
            await fetchAIResponse(text);

            // 4. Stop loading and enable input (only if no new options are displayed and input area is still visible)
            if (optionContainer.children.length === 0 && inputControlArea.style.display !== 'none') {
                toggleLoading(false);
                userInput.focus();
            }
        }

        sendButton.addEventListener('click', () => handleSend(null, false));
        userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !sendButton.disabled && optionContainer.children.length === 0) {
                handleSend(null, false);
            }
        });
        
        document.addEventListener('DOMContentLoaded', () => {
            const checkAuth = setInterval(() => {
                if (isAuthReady) {
                    clearInterval(checkAuth);
                    userInput.focus();
                    sendButton.disabled = false; 
                }
            }, 100);
        });

    </script>
</body>
</html>
