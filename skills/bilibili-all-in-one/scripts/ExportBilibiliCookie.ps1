# Export Bilibili Cookie from Chrome
# Run this after logging into bilibili.com in Chrome

$CookiePath = "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Cookies"
$OutputFile = "F:\Workspace\Deepseek Harness\2026825\bilibili_cookies.txt"

Write-Host "=== Bilibili Cookie Export ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Please follow these steps:" -ForegroundColor Yellow
Write-Host "1. Open Chrome and go to bilibili.com"
Write-Host "2. Make sure you are logged in"
Write-Host "3. Press F12 to open DevTools"
Write-Host "4. Go to Application tab > Cookies > https://www.bilibili.com"
Write-Host "5. Find 'SESSDATA' cookie and copy its value"
Write-Host ""
Write-Host "Or use this PowerShell command to read Chrome cookies:" -ForegroundColor Green
Write-Host ""

# Alternative: Use Python to read Chrome cookies
Write-Host "Running Python cookie reader..." -ForegroundColor Yellow
& "C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" -c "
import browser_cookie3
import json

try:
    cj = browser_cookie3.chrome(domain_name='.bilibili.com')
    cookies = {}
    for cookie in cj:
        cookies[cookie.name] = cookie.value
    
    # Save cookies
    with open(r'$OutputFile', 'w') as f:
        json.dump(cookies, f, indent=2)
    
    print(f'Exported {len(cookies)} cookies to $OutputFile')
    if 'SESSDATA' in cookies:
        print('SESSDATA found!')
    else:
        print('SESSDATA not found - please login to bilibili.com first')
except Exception as e:
    print(f'Error: {e}')
    print('Please install browser_cookie3: pip install browser_cookie3')
" 2>&1

Write-Host ""
Write-Host "=== Done ===" -ForegroundColor Cyan
