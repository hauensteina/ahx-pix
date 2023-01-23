
'use strict;'

// Make an image carousel from the .ahx-slide elements in <div id=containerId...>
// Example: AHXCarousel('#ahx-carousel')
class AHXCarousel {
  constructor( containerId) {
    this.container = document.querySelector(containerId)
    // Properties
    this.prevSlide = null

    this.container.querySelector('.ahx-carousel-button.ahx-next').addEventListener( 'click', ev => { this._changeImage('next') } )
    this.container.querySelector('.ahx-carousel-button.ahx-prev').addEventListener( 'click', ev => { this._changeImage('prev') } )
    this._preventClickOnPrevious()
    this._enableSwiping()
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
    //const slides = this.container.querySelectorAll('.ahx-slide')
    //var activeSlide = this.container.querySelector('.ahx-slide.ahx-active') 
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

  // Prevent click action on previous slide.
  // Otherwise swiping will restart a video.
  //------------------------------------------
  _preventClickOnPrevious() {
    this.slides().forEach( imgOrVideo => {
      imgOrVideo.addEventListener( 'click', (ev) => {
        if (this.prevSlide === ev.target) {
          console.log('prevent')
          ev.preventDefault()
        }
      }) 
    })
  } // _preventClickOnPrevious()

} // class AHXCarousel

