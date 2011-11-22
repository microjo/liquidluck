/*
 * @author lepture
 * @website http://lepture.com
 * @require jquery.js
 */
if(window.jQuery){(function($){
    $(function(){
        var isMobile = navigator.userAgent.match(/(iPhone|iPod|Android|Blackberry|mobile)/);
        var currentNav = window.currentNav || '#nav-home';
        $(currentNav).addClass('current');
        if(!isMobile) {
            $(document).keydown(function(e) {
                var tagName = e.target.tagName.toLowerCase();
                if("input" == tagName|| "textarea" == tagName){return ;}
                if(37 == e.keyCode || 72 == e.keyCode){
                    var url = $('#prev-entry').attr('href');
                }else if(39 == e.keyCode || 76 == e.keyCode){
                    var url = $('#next-entry').attr('href');
                }
                var url = url || '';
                if(url){location.assign(url);}
            });
        }
        if($('div.rdbWrapper').length && !isMobile) {
            $('#footer').after('<script type="text/javascript" src="http://www.readability.com/embed.js" async></script>');
        }
        if(isMobile) {
            $('#search-form').hide();
            $('#header nav, #nav li').height(36);
            $('#nav a').css({fontSize: 13, lineHeight: '36px'});
        }
    });
})(jQuery);}
