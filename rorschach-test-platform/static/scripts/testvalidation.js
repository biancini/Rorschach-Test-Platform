$(document).ready(function() {
	var standardLikert = "Strongly disagree|Disagree|Neither agree nor disagree|Agree|Strongly agree";
	
	startdate = $('#teststartdate').val();
	$('#teststartdate').datepicker();
	$('#teststartdate').datepicker("option", "dateFormat", "dd/mm/yy");
	$('#teststartdate').val(startdate);
	
	enddate = $('#testenddate').val();
	$('#testenddate').datepicker();
	$('#testenddate').datepicker("option", "dateFormat", "dd/mm/yy");
	$('#testenddate').val(enddate);
	
	$('#testForm').children('div').each(function() {
		if ($(this).attr('field') != "send") {
			$('#' + $(this).attr('field')).blur(validateForm);
			$('#' + $(this).attr('field')).keyup(validateForm);
			$('#' + $(this).attr('field')).change(validateForm);
		}
	});
	
	$('#send').click(function() {
		if (validateForm()) {
			valQuestions = ""; $('#questions option').each(function(){ valQuestions += $(this).val() + "\n"; });
			$('#questions_list').val(valQuestions); 
			$('#testForm').submit();
		}
	});
	validateForm();
	
	function validateForm() {
		valid = true;		
		$('#testForm').children('div').each(function() { if ($(this).attr('field') != null) { if ($(this).attr('field') != "send") valid = valid & validateInput($(this).attr('field')); }});
		if (valid) { $('#testFormError').hide(); $('#testFormInfo').show(); $('#send').removeClass('error'); }
		else { $('#testFormError').show(); $('#testFormInfo').hide(); $('#send').addClass('error'); }
		return valid;
	}
	
	function validateInput(name) {
		if (eval("validate_" + name + "()")) { $('#' + name).addClass('error'); $('#' + name + 'Info').hide(); $('#' + name + 'Error').show(); return false; }
		else { $('#' + name).removeClass('error'); $('#' + name + 'Info').show(); $('#' + name + 'Error').hide(); return true; }
	}
	
	function validate_testname() {
		return $('#testname').val().trim().length <= 5;
	}
	
	function validate_testdescription() {
		return $('#testdescription').val().trim().length <= 20;
	}
	
	function validate_teststartdate() {
		if ($('#teststartdate').val().trim() == "") return true;
		try {
			$.datepicker.parseDate('dd/mm/yy', $('#teststartdate').val());
			return false; 
		}
		catch(err) { return true; }
	}
	
	function validate_testenddate() {
		if ($('#testenddate').val().trim() == "") return true;
		if ($('#teststartdate').val().trim() == "") return true;
		try {
			return ($.datepicker.parseDate('dd/mm/yy', $('#testenddate').val()) < $.datepicker.parseDate('dd/mm/yy', $('#teststartdate').val()));
		}
		catch(err) { return true; }
	}
	
	function validate_testfile() {
		return false;
	}
	
});

