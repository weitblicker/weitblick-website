  $(document)
    .ready(function() {

      // fix menu when passed
      $('.masthead')
        .visibility({
          once: false,
          onBottomPassed: function() {
            $('.fixed.menu').transition('fade in');
          },
          onBottomPassedReverse: function() {
            $('.fixed.menu').transition('fade out');
          }
        })
      ;

      // create sidebar and attach to menu open
      $('.ui.sidebar')
        .sidebar('attach events', '.toc.item')
      ;

    
      $('#popup-menu-btn')
      .popup({
        popup      : $('#popup-menu'),
        on         : 'click', 
        hoverable  : true,
        inline     : false,
        transition : 'fade',
        delay: {
          show: 300,
          hide: 800
        }
      });

      $('#popup-menu-2-btn')
      .popup({
        popup      : $('#popup-menu-2'),
        on         : 'click', 
        hoverable  : true,
        inline     : false,
        transition : 'fade',
        delay: {
          show: 300,
          hide: 800
        }
      });


    });

