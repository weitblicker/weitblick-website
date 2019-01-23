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
              url: '/ajax/search/{query}'
          },
          type: 'category',
          minCharacters: 3,
      });

      var news_filter_union = "";
      var news_filter_search = "";

      var filter_news = function(union, search){
        $.ajax({
          url: '/ajax/filter-news/',
          data: {
            'union': union,
            'contains': search,
          },
          dataType: 'html',
          success: function (data) {
            $('#news-list').children().fadeOut('fast');
            $('#news-list').html(data)
            $('#news-list').children().fadeIn('fast');
          },
          error: function(error){
            console.log(error)
          }
        }); 
      }

      $('#news-filter-hosts')
        .dropdown({
          allowAdditions: true,
          onChange: function(value, text, choice){
            news_filter_union = value;
            console.log("Search",news_filter_union, news_filter_search);
            filter_news(news_filter_union, news_filter_search);
          },
      });

      $('#news-filter-search').on("change paste keyup", function() {
        news_filter_search = $(this).val();
        console.log("Search",news_filter_union, news_filter_search);
        filter_news(news_filter_union, news_filter_search);
      });
    });

