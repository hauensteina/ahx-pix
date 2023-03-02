
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

/* Get rendered size of image after abject-fit:contain; */
function getContainedFrame(img) {
  if (img.tagName == 'IMG') {
    var ratio = img.naturalWidth / img.naturalHeight
  } else { // video
    //debugger
    var ratio = img.videoWidth / img.videoHeight
  }
  var h = document.body.clientHeight
  var w = document.body.clientWidth
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


