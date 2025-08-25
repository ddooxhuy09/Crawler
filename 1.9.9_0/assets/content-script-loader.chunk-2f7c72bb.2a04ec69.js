(function () {
  'use strict';

  (async () => {
    await import(
      /* @vite-ignore */
      chrome.runtime.getURL("assets/chunk-2f7c72bb.js")
    );
  })().catch(console.error);

})();
