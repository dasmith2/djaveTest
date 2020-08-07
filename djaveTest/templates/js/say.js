// This sounds way better in Chrome than in Firefox, but I just could not get
// it to work in the chromium browser Selenium starts.
// https://stackoverflow.com/questions/46863170/speechsynthesis-getvoices-is-empty-array-in-chromium-fedora

$(function() {
  window.done_talking = false;
  window.talking = window.talking || {};
  var utterance = new SpeechSynthesisUtterance('{{ say_this }}');
  window.talking[utterance.text] = true;
  utterance.onend = function (event) {
    window.talking[utterance.text] = false;
    var still_talking = false;
    for (var text in window.talking) {
      still_talking = still_talking || window.talking[text];
    }
    window.done_talking = !still_talking;
  }
  // The voice is hard to understand in Firefox. Slowing down from 1 to .9 helps
  // a little.
  utterance.rate = 0.9;
  speechSynthesis.speak(utterance);
});
