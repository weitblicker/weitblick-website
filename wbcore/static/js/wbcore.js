$(document)
    .ready(function() {

        $("body").on('DOMSubtreeModified', ".martor-preview", function() {
            $('.menu .item').tab();
        });

        $('#language-dropdown').dropdown();

        $('.menu .item').tab();

        $('.ui.calendar')
            .calendar({
                type: 'date',
                monthFirst: false,
                startMode: 'year',
                formatter: {
                    date: function (date, settings) {
                        if (!date) return '';
                        var day = date.getDate();
                        var month = date.getMonth() + 1;
                        var year = date.getFullYear();
                        return day + '.' + month + '.' + year;
                    }
                }
        });

        $('.sticky').sticky(
            {
                context:'#main',
                offset: 24,
            }
        );

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

        $('.popup-menu-btn').click(function(){
            $('.icon', this).toggleClass("halfway flipped rotated")  ;
            $('#popup-menu').slideToggle();
        });

        $('.ui.search').search({
            apiSettings: {
                url: '/ajax/search/{query}'
            },
            type: 'category',
            minCharacters: 3,
        });

        $('#search').find('.dropdown').dropdown(
            {
                onChange: function (value, text, choice) {
                    console.log(value);
                }
            }
        );

        $('#search').search(
            {
                type: 'category',
                selector:{
                    results: '.results',
                },
                searchOnFocus: true,
                transition: 'fade-in',
                apiSettings: {
                    url: '/ajax/search/{query}',
                    onResponse: function(results) {
                        console.log(results);
                    }
                },
                onSearchQuery: function (query) {
                    console.log(query);
                }
            }
        );


        let filter_union = "";
        if(filter_union_preset) filter_union = filter_union_preset;
        let filter_search = "";
        let filter_country = "";
        let filter_visibility = "";
        let filter_from = "";
        let filter_to = "";

        let filter = function(){
            console.log($('#filter').data('ajax-endpoint'));
            console.log("Filter union:", filter_union, "search: ", filter_search,
                "country:", filter_country, "visibility:", filter_visibility);
            data = {};
            if(filter_union) data['union'] = filter_union;
            if(filter_search) data['search'] = filter_search;
            if(filter_country) data['country'] = filter_country;
            if(filter_visibility) data['visibility'] = filter_visibility;
            if(filter_from) data['from'] = filter_from;
            if(filter_to) data['to'] = filter_to;
            $.ajax({
                url: $('#filter').data('ajax-endpoint'),
                data: data,
                dataType: 'html',
                success: function (data) {
                    console.log("success...", data)
                    let item_list = $('#item-list');
                    item_list.children().fadeOut('fast');
                    item_list.html(data);
                    item_list.children().fadeIn('fast');
                },
                error: function(error){
                    console.log(error)
                }
            });
        };

        $('#filter-clear').on('click', function() {
            $('#filter-hosts').dropdown('clear');
            filter_union = "";
            if(filter_union_preset) {
                filter_union = filter_union_preset;
                $('#filter-hosts').dropdown('set selected', filter_union_preset);
            }
            $('#filter-from').calendar('clear');
            filter_from = "";
            $('#filter-to').calendar('clear');
            filter_to = "";
            $('#filter-country').dropdown('clear');
            filter_country = "";
            $('#filter-visibility').dropdown('clear');
            filter_visibility = "";
            $('#filter-search').val('');
            filter_search = "";
            filter();
        });

        $('#filter-hosts')
            .dropdown({
                onChange: function(value, text, choice){
                    filter_union = value;
                    filter();
                },
            });

        $('#filter-from')
            .calendar({
                type: 'month',
                startMode: 'month',
                onChange: function(value, text, choice){
                    if (value) {  // needed so no error occurs during clearing the filter
                        filter_from = value.getFullYear() + '-' + (value.getMonth() + 1);
                        console.log(value, text, choice);
                        filter();
                    };
                },
            });

        $('#filter-to')
            .calendar({
                type: 'month',
                startMode: 'month',
                onChange: function(value, text, choice){
                    if (value) {  // needed so no error occurs during clearing the filter
                        filter_to = value.getFullYear() + '-' + (value.getMonth() + 1);
                        console.log(value, text, choice);
                        filter();
                    }
                },
            });

        $('#filter-search').on("change paste keyup", function() {
            filter_search = $(this).val();
            filter();
        });

        $('#filter-visibility')
            .dropdown({
                onChange: function(value, text, choice){
                    filter_visibility = value;
                    filter();
                },
            });

        $('#filter-country')
            .dropdown({
                onChange: function(value, text, choice){
                    filter_country = value;
                    filter();
                },
            });
    });

