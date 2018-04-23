$(document).ready(function(){
  $('.home-managers__slick').slick({
    slidesToShow: 5,
    slidesToScroll: 1,
    centerMode: true,
    centerPadding: '5rem',
    infinite: true,
    dots: true,
    accessibility: false,
    responsive: [
      {
        breakpoint: 1350,
        settings: {
          slidesToShow: 3
        }
      },
      {
        breakpoint: 900,
        settings: {
          slidesToShow: 1,
          centerPadding: '10rem'
        }
      },
      {
        breakpoint: 600,
        settings: {
          slidesToShow: 1,
          centerPadding: '5rem'
        }
      }
    ]
  });
});

$(document).ready(function(){
  $('.home-projects__slick').slick({
    slidesToShow: 5,
    slidesToScroll: 3,
    centerMode: true,
    centerPadding: '10rem',
    infinite: true,
    dots: true,
    accessibility: false,
    responsive: [
      {
        breakpoint: 1350,
        settings: {
          slidesToShow: 1,
          centerPadding: '20rem'
        }
      },
      {
        breakpoint: 900,
        settings: {
          slidesToShow: 1,
          centerPadding: '15rem'
        }
      },
      {
        breakpoint: 600,
        settings: {
          slidesToShow: 1,
          centerPadding: '5rem'
        }
      }
    ]
  });
});