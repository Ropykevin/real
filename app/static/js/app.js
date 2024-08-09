$(document).ready(function () {
    $('.onclick').on('click', function () {

        var member_id = $(this).attr('member_id');

        var id = $('#topic'+member_id)

        req = $.ajax({
            url : '/getData',
            type: 'POST',
            data: {id:member_id}
        });

        $('$contentSection'+member_id).fadeOut(1000).fadeIn(1000);

    });
});