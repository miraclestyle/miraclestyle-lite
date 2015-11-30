chrome.app.runtime.onLaunched.addListener(function(launchData) {
    chrome.app.window.create('index.html', {
        id: "GDriveExample",
        innerBounds: {
            width: 1024,
            height: 768,
            minWidth: 640,
            minHeight: 480
        },
        frame: 'none'
    });
});

chrome.runtime.onInstalled.addListener(function() {
    console.log('installed');
});

chrome.runtime.onSuspend.addListener(function() {
    // Do some simple clean-up tasks.
});
