(function () {
  'use strict';

  (async () => {
    await import(
      /* @vite-ignore */
      chrome.runtime.getURL("assets/chunk-f8f52f07.js")
    );
  })().catch(console.error);

})();
