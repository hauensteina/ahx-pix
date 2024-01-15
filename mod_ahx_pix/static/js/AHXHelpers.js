
'use strict;'

/* Shorthand for document.querySelector */
function E( selector) { 
  return document.querySelector( selector)
}

/* Shorthand for document.querySelectorAll */
function A( selector) {
  // Convert to array before returning
  return [ ...document.querySelectorAll( selector) ]
}

/* Shorthand for obj.querySelectorAll */
function AO( obj, selector) {
  // Convert to array before returning
  return [ ...obj.querySelectorAll( selector) ]
}

/* Check whether we're on a phone or pad */
function isMobile() {
  const isMobile = 'ontouchstart' in window || navigator.maxTouchPoints > 0 || navigator.msMaxTouchPoints > 0
  return isMobile
}

/* Get rendered size of image after object-fit:contain; */
function getContainedFrame(img) {
  if (img.tagName == 'IMG') {
    var ratio = img.naturalWidth / img.naturalHeight
  } else { // video
    //debugger
    var ratio = img.videoWidth / img.videoHeight
  }
  // var h = document.body.clientHeight
  // var w = document.body.clientWidth
  var h = img.clientHeight
  var w = img.clientWidth
  var width = h * ratio
  var height = h
  if (width > w) {
    width = w
    height = w / ratio
  }
  var midX = w / 2.0
  var midY = h / 2.0
  var left = midX - width / 2.0   
  var top = midY - height / 2.0   
  //console.log( `WHTL:${width} ${height} ${top} ${left}`) 
  return { 'width':width, 'height':height, 'top':top, 'left':left } 
} // getContainedFrame()

function isLandscape() {
  return window.innerWidth > window.innerHeight
} // isLandscape()
