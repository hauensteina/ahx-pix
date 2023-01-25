
'use strict;'

// Make an image carousel from the .ahx-slide elements in <div id=containerId...>
// Example: AHXCarousel('#ahx-carousel')
class AHXCarousel {
  constructor( containerId) {
    this.container = document.querySelector(containerId)
    // Properties
    this.prevSlide = null
    this.arrowTimer = null

    this.container.querySelector('.ahx-carousel-button.ahx-next').addEventListener( 'click', ev => { this._changeImage('next') } )
    this.container.querySelector('.ahx-carousel-button.ahx-prev').addEventListener( 'click', ev => { this._changeImage('prev') } )
    this._preventClickOnPrevious()
    this._enableSwiping()
    this._enableKeyNav()
    this._hideArrows()
  }

  //--------------------
  slides() {
    return this.container.querySelectorAll( '.ahx-slide')
  }

  //--------------------
  activeSlide() {
    return this.container.querySelector( '.ahx-slide.ahx-active')
  }

  //------------------------------------------------------
  _changeImage( direction) {
    var offset = 1
    if (direction == 'prev') offset = -1
    var activeSlide = this.activeSlide()
    var slides = this.slides()
    this.prevSlide = activeSlide

    let newIndex = [...slides].indexOf(activeSlide) + offset

    if (newIndex < 0) { newIndex = slides.length - 1 }
    if (newIndex >= slides.length) { newIndex = 0 }
    var nextSlide = slides[newIndex]
    nextSlide.classList.add( 'ahx-active')
    if (activeSlide.tagName == 'VIDEO') {
      activeSlide.pause()
      console.log('pause')
    }
    if (nextSlide.tagName == 'VIDEO') {
      nextSlide.play()
      console.log('play')
    }
    activeSlide.classList.remove( 'ahx-active')
    this._resetArrowTimer()
  } // _changeImage()

  //-------------------------------
  _enableSwiping() {
    var downX = 0
    var upX = 0
    this.slides().forEach( imgOrVideo => {
      imgOrVideo.onpointerdown = ev => {
        ev.preventDefault()
        downX = ev.clientX
      }
      imgOrVideo.onpointerup = ev => {
        ev.preventDefault()
        upX = ev.clientX
        if (Math.abs(upX - downX) < 10) return
        if (upX > downX) { this._changeImage('prev') }
        else { this._changeImage('next') }
      }
    }) // slides.foreach
  } // _enableSwiping()

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

  // Hide arrows after a timeout; show on mouse move
  //--------------------------------------------------
  _hideArrows() {
    var self = this
    // self.container.addEventListener( 'mousemove', () => {
    //   document.querySelector('.ahx-carousel-button.ahx-next').hidden = false
    //   document.querySelector('.ahx-carousel-button.ahx-prev').hidden = false
    //   self._resetArrowTimer()
    // })
    this._resetArrowTimer()
  } // hideArrows()

  //---------------------------
  _resetArrowTimer() {
    const TIMEOUT = 2500
    function timerFired() {
      document.querySelector('.ahx-carousel-button.ahx-next').hidden = true
      document.querySelector('.ahx-carousel-button.ahx-prev').hidden = true
    }
    clearTimeout(this.arrowTimer )
    this.arrowTimer = setTimeout( timerFired, TIMEOUT)
  } // _resetArrowTimer()

  // Prevent click action on previous slide.
  // Otherwise swiping will restart a video.
  //------------------------------------------
  _preventClickOnPrevious() {
    this.slides().forEach( imgOrVideo => {
      imgOrVideo.addEventListener( 'click', (ev) => {
        if (this.prevSlide === ev.target) {
          //console.log('prevent')
          ev.preventDefault()
        }
      }) 
    })
  } // _preventClickOnPrevious()

} // class AHXCarousel

