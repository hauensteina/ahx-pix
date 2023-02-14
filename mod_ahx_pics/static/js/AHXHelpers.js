
'use strict;'

/* Shorthand for document.querySelector */
function E( selector) { 
  return document.querySelector( selector)
}

/* Shorthand for document.querySelectorAll */
function A( selector) { 
  return document.querySelectorAll( selector)
}

/* Check whether we're on a phone or pad */
function isMobile() { return typeof window.orientation !== 'undefined' }

