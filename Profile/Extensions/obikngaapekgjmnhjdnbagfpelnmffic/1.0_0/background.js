// Default settings
const defaultSettings = {
  enabled: false,
  elementSelector: "",
  iframeElementSelector:"",
  interval: 60,
};
appData = {
  siteSettings: [],
};
// Refresh or Keep Active enabled sites at specified intervals
function clickElementsOnSites(sites) {
  sites.forEach(function (site) {
    if (site.timerId != 0) {
      clearInterval(site.timerId);
      site.timerId = 0;
    }
    if (site.enabled) {
      console.log(
        site.siteHost + " is enabled for selector " + site.elementSelector
      );
      if (site.elementSelector != "" || site.elementSelector != null) {
        if(site.iframeElementSelector == undefined)
        site.iframeElementSelector = "";
        site.timerId = setInterval(function () {
          clickElement(
            site.siteHost,
            site.elementSelector,
            site.iframeElementSelector
          );
        }, site.interval * 1000);
      }
    }
  });
  chrome.storage.local.set({ settings: sites }, function () {});
}

function clickElement(hostName, selector, iframeSelector) {
  var query = "*://" + hostName + "/*";
  chrome.tabs.query({ url: query }, function (tabs) {
    tabs.forEach(function (tab) {
      chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: (hostName, selector, iframeSelector) => {
          if (iframeSelector == undefined || iframeSelector == "" || iframeSelector == null) {
            var elementFromQuery = document.querySelector(selector);
            if (elementFromQuery != null || elementFromQuery != undefined) {
              console.log(
                "Clicked selector '" + selector + "' on site: " + hostName
              );
              elementFromQuery.click();
            }
          } else {
            var iframeElement = document.querySelector(iframeSelector);
                var iframeDoc = iframeElement.contentWindow.document;

                var elementInsideIframe = iframeDoc.querySelector(selector);
                if (elementInsideIframe != null || elementInsideIframe != undefined) {
                  console.log(
                    "Clicked selector '" + selector + "' from inside Iframe on site: " + hostName
                  );
                  elementInsideIframe.click();
                }

            var elementFromQuery = document.querySelector(selector);
            if (elementFromQuery != null || elementFromQuery != undefined) {
              console.log(
                "Clicked selector '" + selector + "' on site: " + hostName
              );
              elementFromQuery.click();
            }
          }
        },
        args: [hostName, selector, iframeSelector], // pass any parameters to function
      });
    });
  });
}

// Retrieve settings from storage
function getSettings(callback) {
  chrome.storage.local.get(
    { settings: this.appData.siteSettings },
    function (data) {
      callback(data);
    }
  );
}

// Save settings to storage
function saveSettings(settings, callback) {
  this.appData.siteSettings = [];
  getSettings(function (data) {
    if (data && data.settings) {
      var oldData = data.settings.find((x) => x.siteHost == settings.siteHost);
      if (oldData != undefined) {
        var oldTimerId = oldData.timerId;
        settings.timerId = oldTimerId;
        this.appData.siteSettings = data.settings.filter(
          (x) => x.siteHost != settings.siteHost
        );
      } else {
        this.appData.siteSettings = data.settings;
      }
      this.appData.siteSettings.push(settings);
    } else {
      this.appData.siteSettings.push(settings);
    }

    chrome.storage.local.set(
      { settings: this.appData.siteSettings },
      function () {
        clickElementsOnSites(this.appData.siteSettings || []);
        callback({ success: true, message: "Settings saved successfully" });
      }
    );
  });
}

// Message handler
chrome.runtime.onMessage.addListener(function (request, sender, sendResponse) {
  if (request.action === "saveSettings") {
    saveSettings(request.settings, sendResponse);
    return true; // Indicates the response will be sent asynchronously
  } else if (request.action === "getSettings") {
    getSettings(sendResponse);
    return true; // Indicates the response will be sent asynchronously
  }
});

// Initialize settings on extension installation
chrome.runtime.onInstalled.addListener(function (details) {
  if (details.reason === "install") {
    console.log("Install");
  }
});
