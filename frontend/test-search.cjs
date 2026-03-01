const puppeteer = require('puppeteer');
(async () => {
    const browser = await puppeteer.launch({args: ['--no-sandbox']});
    const page = await browser.newPage();
    page.setDefaultTimeout(15000);
    page.on('console', msg => console.log('LOG:', msg.text()));
    await page.goto('http://localhost:5174', {waitUntil: 'networkidle0'});
    
    try {
        await page.evaluate(() => {
            const inputs = document.querySelectorAll('input, textarea');
            for(let el of inputs) {
                if(el.placeholder && el.placeholder.includes('Try')) {
                    el.value = 'A trip to Rajasthan';
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                }
            }
        });
        
        await page.evaluate(() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const searchBtn = btns.find(b => b.textContent && b.textContent.includes('Generate Trip'));
            if(searchBtn) searchBtn.click();
        });
        
        await new Promise(r => setTimeout(r, 4000));
        
        const errorBoundary = await page.evaluate(() => {
            const details = document.querySelector('details');
            return details ? details.innerText : 'No error boundary details found';
        });
        console.log("CRASH LOG:\n", errorBoundary);
        
    } catch(e) { console.log("Script error", e.message); }
    
    await browser.close();
})();
