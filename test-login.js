// Test script para console do navegador
async function testAdminLogin() {
  try {
    // Step 1: Frontend validation and temp token generation
    const email = 'admin@vagasync.com';
    const password = 'admin123';
    console.log('✅ Dev Credentials Detected');
    const tempToken = 'dev-temp-token-' + Date.now();
    console.log('🔑 Generated temp token:', tempToken);
    
    // Step 2: Call backend 2FA endpoint
    const response = await fetch('http://localhost:8000/api/admin/verify-2fa', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        temp_token: tempToken, 
        code: '123456' 
      })
    });
    
    console.log('📡 Backend response status:', response.status);
    const data = await response.json();
    console.log('✅ Backend response:', data);
    
    if (response.ok) {
      console.log('🎉 Login successful! Access token:', data.access_token?.substring(0, 20) + '...');
    } else {
      console.error('❌ Backend error:', data.detail);
    }
  } catch(e) {
    console.error('❌ Error:', e.message);
  }
}
testAdminLogin();
