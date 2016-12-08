
function main() {

(function () {
   'use strict';
   
  	$('a.page-scroll').click(function() {
        if (location.pathname.replace(/^\//,'') == this.pathname.replace(/^\//,'') && location.hostname == this.hostname) {
          var target = $(this.hash);
          target = target.length ? target : $('[name=' + this.hash.slice(1) +']');
          if (target.length) {
            $('html,body').animate({
              scrollTop: target.offset().top
            }, 900);
            return false;
          }
        }
      });

    // Show Menu on Book
    $(window).bind('scroll', function() {
        var navHeight = $(window).height() - 500;
        if ($(window).scrollTop() > navHeight) {
            $('.navbar-default').addClass('on');
        } else {
            $('.navbar-default').removeClass('on');
        }
    });

    $('body').scrollspy({ 
        target: '.navbar-default',
        offset: 80
    });
	
	
	// Hide nav on click
  $(".navbar-nav li a").click(function (event) {
    // check if window is small enough so dropdown is created
    var toggle = $(".navbar-toggle").is(":visible");
    if (toggle) {
      $(".navbar-collapse").collapse('hide');
    }
  });

  	// Portfolio isotope filter
    $(window).load(function() {
        var $container = $('.portfolio-items');
        $container.isotope({
            filter: '*',
            animationOptions: {
                duration: 750,
                easing: 'linear',
                queue: false
            }
        });
        $('.cat a').click(function() {
            $('.cat .active').removeClass('active');
            $(this).addClass('active');
            var selector = $(this).attr('data-filter');
            $container.isotope({
                filter: selector,
                animationOptions: {
                    duration: 750,
                    easing: 'linear',
                    queue: false
                }
            });
            return false;
        });

    });

  	// Pretty Photo
	$("a[rel^='prettyPhoto']").prettyPhoto({
		social_tools: false
	});	

}());


}
main();

$(document).ready(function () {
 


 // Polling function
  var polling = function (task_id) {
    
    $.get('/result/' + task_id, function (data) {
      if (data.ready) {
        $('#result').html(data.result);
      } else {
        
        setTimeout(function () {
          $('#result').html('Архив обрабатывается');  
          polling(task_id);

        }, 1000);
           $('#result_header').show();
           $('#result').show();
           $('html,body').animate({
                  scrollTop: $('#result').offset().top -150
                  }, 500);
      }

    });
    
  };

$('#upload-file-btn').click(function() {
        var form_data = new FormData($('#upload-file')[0]);
        $.ajax({
            type: 'POST',
            url: '/uploadajax',
            data: form_data,
            contentType: false,
            cache: false,
            processData: false,
            async: false,
            success: function(data) {
                console.log('Success!');
                polling(data.task_id);
            },
            
            
        });
        
    
    });


  $('#recognize').click(function () {
    
    console.log($('#message').val());
    request = $.ajax({
      url:'/process_text',
      type: 'POST',
      data: $('form').serialize(),
      success: function(response) {
                var d = JSON.parse(response);
                $('#result').html(d.text);
                $('#result_header').show();
                $('#result').show();
                $('html,body').animate({
                  scrollTop: $('#result').offset().top -150
                  }, 400);
            },
      error: function(error) {
          console.log(error);
      }
        
    });

      return false
  });
});

// $(document).ready(function () {
//   var click_count = 0;
//   $('#recognize').click(function () {
//     click_count += 1
//     $.get('/data?cc=' + click_count, function(data) {
//       var string = '<tr><td>' + click_count + '</td><td>' + data.a + '</td></tr>';
//       $('.ourtable > tbody').append(string);
//     });
//     return false;
//   });
// });
