var loginWindowTimer;
var facebookLoginWindow;

function fb_login(area) {
	if (area == undefined) area = 'fb_login';
	action = $('#' + area).attr('action');
	callback = $('#' + area).attr('callback');

	var popupWidth=450;
	var popupHeight=300;
	var xPosition=($(window).width()-popupWidth)/2;
	var yPosition=($(window).height()-popupHeight)/2;

	facebookLoginWindow=window.open(
		action + '&load',
		"Facebook",
		"location=0,scrollbars=0,width="+popupWidth+",height="+popupHeight+","+"left="+xPosition+",top="+yPosition
	);

	if (callback == undefined) loginWindowTimer=setInterval('CheckLoginWindowClosure()', 500);
	else loginWindowTimer=setInterval('CheckLoginWindowClosure(callback)', 500);
	return false;
}

function fb_unlink() {
	url = $('#fb_login').attr('action');
	if (url == '') return false;
	$.ajax({type:'GET', url:url,
		success: function(data) {
			$('#fb_area').html(data);
			$('#fb_area').css('display','block');
		}
	});
}

function getFbStatus(){
	url = $('#fb_area').attr('action');
	if (url == '') return false;
	$.ajax({type:'GET', url:url,
		success: function(data) {
			if (data !== '') {
				$('#fb_area').html(data);
				$('#fb_area').css('display','block');
			}
		}
	});
}

function do_login(area){
	if (area == undefined) area = 'fb_area';
	url = $('#' + area).attr('action');
	if (url == '') return false;
	$.ajax({type:'GET', url:url, dataType:'json',
		success: function(data) {
			$('#' + area).html(data.html);
			$('#' + area).css('display','block');
			if (data.url !== undefined) {
				top.location = data.url;
			}
		}
	});
}

function do_login_top(){
	do_login('fb_area_top');
}

function getFbData(){
	url = $('#fb_area').attr('action') + '&getdata';
	url = url.replace('refreshbuttons&','');
	if (url == '') return false;
	$.ajax({type:'GET', url:url, dataType:'json',
		success: function(data) {
			if(!data.status) return false;
			if(data.status == 0) return false;
			if(data.status == -1) {
				alert('Ta facebook račun je že povezan z bolhinim računom. Vsak bolhin račun je lahko povezan le z enim facebook računom.');
				return false;
			}
			if(!data.data) return false;
			$.each(data.data, function(fld, val) {
				$('#' + fld).val(val);
			})
		}
	});
}

function CheckLoginWindowClosure(callback) {
	if (facebookLoginWindow.closed) {
	    clearInterval(loginWindowTimer);
	    if (window.callback) {
			eval(callback + '()');
	    }
	}
}

function fb_napolni_podatke(){
	getFbStatus();
	getFbData();
}

