
'use strict;'

const CAPTION_OFF = 'rgba(100,100,100, .7)'
const CAPTION_ON = 'rgba(255,255,255, .7)'

// Occasionally, try to position the caption 
function captionTimer() {
  g_carousel._positionCaption()
  clearTimeout( captionTimer.timer)
  captionTimer.timer = setTimeout( captionTimer, 200)
}
captionTimer.timer = null 

var g_carousel = ''

// Make an image carousel from the .ahx-slide elements in <div id=containerId...>
// Called from carousel.html
// Example: AHXCarousel('#ahx-carousel')
class AHXCarousel {
  constructor( containerId, galleryId, pictureId) {
    g_carousel = this
    this.container = E(containerId)
    // Properties
    this.galleryId = galleryId
    this.pictureId = pictureId
    this.prevSlide = null
    this.arrowTimer = null

    E('.ahx-carousel-button.ahx-next').addEventListener( 
      'click', ev => { 
        this._changeImage('next') 
        document.body.style.zoom=1.0
      })
    E('.ahx-carousel-button.ahx-prev').addEventListener( 
      'click', ev => { this._changeImage('prev') })
    if (isMobile()) {
      E('.ahx-x').addEventListener( 
        'click', ev => { document.location.href = `/gallery_mobile?gallery_id=${galleryId}` } )
    } else {
      E('.ahx-x').addEventListener( 
        'click', ev => { document.location.href = `/gallery?gallery_id=${galleryId}` } )
    }
    E('.ahx-download').addEventListener(
      'click', ev => { this._downloadImage( this.activeSlide()) })

    E('.ahx-captoggle').addEventListener(
      'click', ev => { 
        if (E('.ahx-captoggle.ahx-active')) {
          let e = E('.ahx-captoggle.ahx-active')
          e.style.color = CAPTION_OFF 
          e.classList.remove( 'ahx-active')
          if (this.activeCaption()) this.activeCaption().style.opacity = 0
        } else {
          let e = E('.ahx-captoggle')
          e.style.color = CAPTION_ON 
          e.classList.add( 'ahx-active')
        }
      })
    if (isMobile()) {
      E('.ahx-carousel-button.ahx-next').hidden = true
      E('.ahx-carousel-button.ahx-prev').hidden = true
    }
    this._preventClickOnPrevious()
    this._enableSwiping()
    this._enableKeyNav()
    this._showArrows()
    this._setImgNum()
    this._preloadImages( this.slides(), this.activeSlide() )
    captionTimer()
    var scroll = window.setInterval(function() { 
      //window.scrollTo(0,100) ; 
    }, 2000) 
  } // constructor

  //------------------
  activeCaption() {
    var activeIdx = [...this.slides()].indexOf(this.activeSlide())
    return E(`#cap_${activeIdx}`) 
  }

  //--------------------
  activeSlide() {
    return E( '.ahx-slide.ahx-active')
  }

  //--------------------
  slides() {
    return A( '.ahx-slide')
  }

  //------------------------------------------------------
  _changeImage( direction) {
    var offset = 1
    if (direction == 'prev') offset = -1
    var activeSlide = this.activeSlide()
    var slides = this.slides()
    this.prevSlide = activeSlide

    var activeIdx = [...slides].indexOf(activeSlide)
    console.log(`>>>>>> change ${activeIdx}`)
    var newIdx = activeIdx + offset    

    var oldCaption = E(`#cap_${activeIdx}`)
    if (oldCaption) oldCaption.style.opacity = 0

    if (newIdx < 0) { newIdx = slides.length - 1 }
    if (newIdx >= slides.length) { newIdx = 0 }
    var nextSlide = slides[newIdx]
    activeSlide.classList.remove( 'ahx-active')
    nextSlide.classList.add( 'ahx-active')
    if (activeSlide.tagName == 'VIDEO') {
      activeSlide.pause()
    }

    this._setImgNum()
    this._resetArrowTimer()
    this._preloadImages(slides, nextSlide)
  } // _changeImage()

  //------------------------------------------------------
  _downloadImage( slide) {
    var url = ''
    if (slide.src.includes('static/images/')) { // not pic or video
      let osrc = slide.getAttribute('data-fname')
      url = '/download_img?q=' + Math.random() + 
        '&slide_src=' + encodeURIComponent(osrc) +
        '&other_type=true'
    } 
    else if (slide.tagName == 'VIDEO') { // video
      let vsrc = E(`#${slide.id} source`).getAttribute('src')     
      url = '/download_img?q=' + Math.random() + 
        '&slide_src=' + encodeURIComponent(vsrc)
    } 
    else { // photo
      let isrc = slide.src
      url = '/download_img?q=' + Math.random() + 
        '&slide_src=' + encodeURIComponent(isrc)
    }
    window.location.href = url
  } // _downloadImage()

  // Key actions. Left/Right arrow navigate thru images.
  // Space pauses a movie.
  //-------------------------------------------------------
  _enableKeyNav(e) {
    const self = this
    function checkKey(e) {
      e = e || window.event;
      if (e.keyCode == '37') { // left arrow
        self._changeImage('prev')
      }
      else if (e.keyCode == '39') { // right arrow
        self._changeImage('next')
      }
      else if (e.keyCode == '32') { // space
        if (self.activeSlide().tagName == 'VIDEO') {
          e.preventDefault()
          let video = self.activeSlide()
          if (!video.paused && !video.ended) {
            video.pause()
          } else {
            video.play()
          }
        } // if
      } // if space
    } // check_key()
    document.onkeydown = checkKey
  } // check_key()

  //-------------------------------
  _enableSwiping() {
    this.slides().forEach( imgOrVideo => {
      imgOrVideo.onpointerdown = ev => {
        ev.preventDefault()
         this.downX = ev.clientX
      }
      imgOrVideo.onpointerup = ev => {
        ev.preventDefault()
        this.upX = ev.clientX
        if (Math.abs(this.upX -  this.downX) < 10) return
        if (this.upX >  this.downX) { this._changeImage('prev') }
        else { this._changeImage('next') }
      }
    }) // slides.foreach
  } // _enableSwiping()

  // Load active image on demand, and some more to the left and right.
  // Unload other stuff by setting display:none (remove ahx-loaded).
  // Otherwise, mobile browsers crash.
  //---------------------------------------------------------------------
  _preloadImages( slides, nextSlide) {
    var nextIdx = [...slides].indexOf(nextSlide)
    // Load current img
    if (!slides[nextIdx].classList.contains('ahx-loaded')) { load( slides[nextIdx], nextIdx) }
    // Load or unload the others
    //for (var idx=0; idx < slides.length; idx++) {
    for (var idx=slides.length-1; idx >= 0; idx--) {
      const slide = slides[idx]
      if (idx >= nextIdx - 2 && idx <= nextIdx + 2 && idx != nextIdx) {
        if (!slide.classList.contains('ahx-loaded')) {
          console.log( `preloading idx ${idx}`)
          load( slide, idx)
        }
      }
      else if (idx != nextIdx) {
        slide.classList.remove( 'ahx-loaded')
      }
    } // for

    function load(elt, idx) {
      elt.classList.add( 'ahx-loaded')
      if (elt.tagName == 'IMG') {
        elt.setAttribute( 'src', elt.getAttribute( 'data-src'))
      }
      else if  (elt.tagName == 'VIDEO') {
        var source = E( `#vsrc_${idx}`)
        if (!source.src) {
          source.src = source.getAttribute('data-src')
          elt.load()
        }
      }
    } // load()
  } // _preloadImages()

  //-----------------------
  _positionCaption() {
    if (!E('.ahx-captoggle.ahx-active')) {
      return
    } 
    var img = this.activeSlide()
    var frame = getContainedFrame(img) 
    img.style.top = `0px`
    if (isNaN(frame.width)) return;
    var caption = this.activeCaption()
    if (!caption) return
    var realWidth = caption.clientWidth
    var realHeight = caption.clientHeight
    caption.style.left = `${frame.left + (frame.width - realWidth)/2.0}px`
    caption.style.top = `${frame.top + frame.height - realHeight - 20 }px`

    caption.style.opacity = 1
  } // _positionCaption()

  // Prevent click action on previous slide.
  // Otherwise swiping will restart a video.
  //------------------------------------------
  _preventClickOnPrevious() {
    this.slides().forEach( imgOrVideo => {
      imgOrVideo.addEventListener( 'click', (ev) => {
        if (this.prevSlide === ev.target) {
          ev.preventDefault()
        }
      }) 
    })
  } // _preventClickOnPrevious()

  // Hide arrows after a timeout; show on mouse move
  //---------------------------------------------------
  _resetArrowTimer() {
    const TIMEOUT = 2000
    function timerFired() { //return;
                            E('.ahx-carousel-button.ahx-next').hidden = true
                            E('.ahx-carousel-button.ahx-prev').hidden = true
                            E('.ahx-x').hidden = true
                            E('#ahx-topcont').hidden = true
                          }
    clearTimeout(this.arrowTimer )
    this.arrowTimer = setTimeout( timerFired, TIMEOUT)
  } // _resetArrowTimer()

  //------------------
  _setImgNum() {
    var slides = this.slides()
    var activeSlide = this.activeSlide()
    var activeIdx = [...slides].indexOf(activeSlide)
    E( '.ahx-imgnum').innerHTML = `${activeIdx+1}/${slides.length}`
  } // _setImgNum

  // Show arrows on mouse move
  //------------------------------
  _showArrows() {
    var self = this
    function showControls() {
      if (!isMobile()) {
        E('.ahx-carousel-button.ahx-next').hidden = false
        E('.ahx-carousel-button.ahx-prev').hidden = false
      }
      E('.ahx-x').hidden = false
      E('#ahx-topcont').hidden = false
      self._resetArrowTimer()
    }
    self.container.addEventListener( 'pointermove', showControls)
    self.container.addEventListener( 'pointerup', showControls)
    this._resetArrowTimer()
  } // showArrows()

} // class AHXCarousel

