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
      /*$('.ui.sidebar')
        .sidebar('attach events', '.toc.item')
      ;*/

      $('#popup-menu-btn').click(function(){
       // $('#popup-menu.show').css('height', $('#popup-menu').first().height());
        $('#popup-menu').slideToggle();
      });

      $('.ui.search').search({
          apiSettings: {
              url: '/search/{query}'
          },
          type: 'category',
          minCharacters: 3,
      });


    });

