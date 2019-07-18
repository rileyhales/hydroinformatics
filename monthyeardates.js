// custom date-picker javascript
/*
pair with <input class="date-picker">
requires jquery UI packages not in tethys
 */
$(function () {
    $('.date-picker').datepicker({
        dateFormat: "mm/yy",
        changeMonth: true,
        changeYear: true,
        showButtonPanel: true,
        onClose: function (dateText, inst) {
            function isDonePressed() {
                return ($('#ui-datepicker-div').html().indexOf('ui-datepicker-close ui-state-default ui-priority-primary ui-corner-all ui-state-hover') > -1);
            }

            if (isDonePressed()) {
                let month = $("#ui-datepicker-div .ui-datepicker-month :selected").val();
                let year = $("#ui-datepicker-div .ui-datepicker-year :selected").val();
                $(this).datepicker('setDate', new Date(year, month, 1)).trigger('change');

                $('.date-picker').focusout()//Added to remove focus from datepicker input box on selecting date
            }
        },
        beforeShow: function (input, inst) {

            inst.dpDiv.addClass('month_year_datepicker');

            if ((datestr = $(this).val()).length > 0) {
                let year = datestr.substring(datestr.length - 4, datestr.length);
                let month = datestr.substring(0, 2);
                $(this).datepicker('option', 'defaultDate', new Date(year, month - 1, 1));
                $(this).datepicker('setDate', new Date(year, month - 1, 1));
                $(".ui-datepicker-calendar").hide();
            }
        }
    })
});